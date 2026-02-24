"""Acoustic solver entry points."""

from __future__ import annotations

from collections.abc import Iterable
import math
from numbers import Real
from typing import Any

__all__ = ["solve_acoustic_submesh"]


def _normalize_boundary_labels(boundary_labels: Iterable[Any]) -> tuple[Any, ...]:
    if isinstance(boundary_labels, (str, bytes)):
        raise TypeError("boundary_labels must be an iterable of labels, not a string.")
    labels = tuple(boundary_labels)
    if not labels:
        raise ValueError("boundary_labels must contain at least one label.")
    return labels


def _dg0_family(mesh: Any) -> str:
    cell = mesh.ufl_cell()
    cell_name_attr = cell.cellname
    cell_name = cell_name_attr() if callable(cell_name_attr) else cell_name_attr
    if cell_name in {"quadrilateral", "hexahedron"}:
        return "DQ"
    return "DG"


def _mesh_topological_dimension(mesh: Any) -> int:
    tdim_attr = mesh.topological_dimension
    return int(tdim_attr() if callable(tdim_attr) else tdim_attr)


def _build_extended_domain_submesh(mesh: Any, label_value: int = 999) -> tuple[Any, int]:
    from firedrake import Function, FunctionSpace, SpatialCoordinate, Submesh, conditional

    DG0 = FunctionSpace(mesh, _dg0_family(mesh), 0)
    indicator_function = Function(DG0)
    x = SpatialCoordinate(mesh)[0]
    indicator_function.interpolate(conditional(x > 0.5, 1, 0))
    mesh.mark_entities(indicator_function, label_value)
    submesh = Submesh(mesh, _mesh_topological_dimension(mesh), label_value)
    if submesh.num_cells() <= 0:
        raise ValueError("Extended-domain Submesh must contain at least one cell.")
    return submesh, label_value


def _coerce_source_term(source: Any) -> Any:
    from firedrake import Constant

    if isinstance(source, Real):
        return Constant(float(source))
    return source


def _coerce_wave_speed_pair(wave_speed: Any) -> tuple[Any, Any]:
    from firedrake import Constant

    if isinstance(wave_speed, Real):
        c = Constant(float(wave_speed))
        return c, c
    return wave_speed, wave_speed


def solve_acoustic_submesh(
    mesh: Any,
    source: Any,
    wave_speed: Any,
    dt: float,
    t_end: float,
    boundary_labels: Iterable[Any],
) -> dict[str, Any]:
    """Solve one or more implicit acoustic steps on a parent mesh and absorbing submesh.

    Parameters
    ----------
    mesh : object
        Parent Firedrake mesh that defines the physical computational domain.
    source : object
        Source term for the pressure equation in the parent domain.
    wave_speed : float or object
        Acoustic wave speed coefficient; scalars must be strictly positive.
    dt : float
        Time-step size used by the implicit update.
    t_end : float
        Final simulation time.
    boundary_labels : Iterable[object]
        Exterior boundary labels on the absorbing submesh where Clayton A1 terms are applied.

    Returns
    -------
    dict[str, object]
        Solver state and metadata, including the extended-domain submesh and finite solution norm.
    """
    if not isinstance(dt, Real) or dt <= 0:
        raise ValueError("dt must be a positive real number.")
    if not isinstance(t_end, Real) or t_end < 0:
        raise ValueError("t_end must be a non-negative real number.")
    if isinstance(wave_speed, Real) and wave_speed <= 0:
        raise ValueError("wave_speed must be positive when provided as a scalar.")

    from firedrake import (
        Constant,
        EquationBC,
        Function,
        FunctionSpace,
        Measure,
        SpatialCoordinate,
        Submesh,
        TestFunctions,
        TrialFunctions,
        assemble,
        conditional,
        grad,
        inner,
        solve,
        split,
    )

    labels = tuple(int(label) for label in _normalize_boundary_labels(boundary_labels))
    extended_submesh, extended_domain_label = _build_extended_domain_submesh(mesh)
    DG0 = FunctionSpace(mesh, _dg0_family(mesh), 0)
    x_parent = SpatialCoordinate(mesh)[0]
    interior_domain_label = extended_domain_label + 1
    interior_indicator = Function(DG0).interpolate(conditional(x_parent <= 0.5, 1, 0))
    mesh.mark_entities(interior_indicator, interior_domain_label)
    interior_submesh = Submesh(mesh, _mesh_topological_dimension(mesh), interior_domain_label)
    if interior_submesh.num_cells() <= 0:
        raise ValueError("Interior Submesh must contain at least one cell.")

    outer_markers = tuple(int(marker) for marker in extended_submesh.exterior_facets.unique_markers)
    parent_boundary_markers = {int(marker) for marker in mesh.exterior_facets.unique_markers}
    interface_markers = tuple(marker for marker in outer_markers if marker not in parent_boundary_markers)
    if not interface_markers:
        if not outer_markers:
            raise ValueError("Extended-domain Submesh must expose boundary labels.")
        interface_markers = (max(outer_markers),)

    interface_marker_set = set(interface_markers)
    outer_marker_set = set(outer_markers)
    clayton_labels = tuple(label for label in labels if label in outer_marker_set and label not in interface_marker_set)
    num_steps = max(1, int(math.ceil(t_end / dt))) if t_end > 0 else 1

    V_outer = FunctionSpace(extended_submesh, "CG", 1)
    V_inner = FunctionSpace(interior_submesh, "CG", 1)
    V = V_outer * V_inner
    u_outer, u_inner = TrialFunctions(V)
    v_outer, v_inner = TestFunctions(V)

    state = Function(V)
    u_outer_prev = Function(V_outer)
    u_inner_prev = Function(V_inner)
    source_term = _coerce_source_term(source)
    c_outer, c_inner = _coerce_wave_speed_pair(wave_speed)

    dx_outer = Measure(
        "dx",
        domain=extended_submesh,
        intersect_measures=(Measure("dx", mesh), Measure("dx", interior_submesh)),
    )
    dx_inner = Measure(
        "dx",
        domain=interior_submesh,
        intersect_measures=(Measure("dx", mesh), Measure("dx", extended_submesh)),
    )
    ds_outer = Measure("ds", domain=extended_submesh, intersect_measures=(Measure("ds", interior_submesh),))
    ds_inner = Measure("ds", domain=interior_submesh, intersect_measures=(Measure("ds", extended_submesh),))

    mass_scale = Constant(1.0 / (dt * dt))
    a = (
        mass_scale * inner(u_outer, v_outer) * dx_outer
        + inner((c_outer * c_outer) * grad(u_outer), grad(v_outer)) * dx_outer
        + mass_scale * inner(u_inner, v_inner) * dx_inner
        + inner((c_inner * c_inner) * grad(u_inner), grad(v_inner)) * dx_inner
        + inner(u_inner, v_outer) * ds_outer(interface_markers)
        + inner(u_outer, v_inner) * ds_inner(interface_markers)
    )

    inv_c_dt = Constant(1.0 / dt) / c_outer
    for label in clayton_labels:
        a += inv_c_dt * inner(u_outer, v_outer) * ds_outer(label)

    L = (
        mass_scale * inner(u_outer_prev, v_outer) * dx_outer
        + mass_scale * inner(u_inner_prev, v_inner) * dx_inner
        + inner(source_term, v_inner) * dx_inner
    )
    for label in clayton_labels:
        L += inv_c_dt * inner(u_outer_prev, v_outer) * ds_outer(label)

    interface_bc = EquationBC(
        inner(u_outer - u_inner, v_outer) * ds_outer(interface_markers)
        == inner(Constant(0.0), v_outer) * ds_outer(interface_markers),
        state,
        interface_markers,
        V=V.sub(0),
    )

    for _ in range(num_steps):
        solve(a == L, state, bcs=[interface_bc])
        solved_outer, solved_inner = state.subfunctions
        u_outer_prev.assign(solved_outer)
        u_inner_prev.assign(solved_inner)

    p_outer, p_inner = split(state)
    norm_sq = assemble(inner(p_outer, p_outer) * dx_outer + inner(p_inner, p_inner) * dx_inner)
    solution_norm = float(math.sqrt(norm_sq))
    if not math.isfinite(solution_norm):
        raise ValueError("Acoustic submesh solve produced a non-finite norm.")

    return {
        "mesh": mesh,
        "extended_submesh": extended_submesh,
        "extended_domain_label": extended_domain_label,
        "interior_submesh": interior_submesh,
        "interior_domain_label": interior_domain_label,
        "source": source,
        "wave_speed": wave_speed,
        "dt": float(dt),
        "t_end": float(t_end),
        "boundary_labels": tuple(labels),
        "clayton_labels": clayton_labels,
        "interface_label": interface_markers,
        "num_steps": num_steps,
        "solution": state,
        "solution_norm": solution_norm,
    }
