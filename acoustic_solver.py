"""Forward acoustic solve helpers for submesh examples."""

from __future__ import annotations

import math
from collections.abc import Iterable
from numbers import Real
from typing import Any


def _ricker_wavelet(time_value: float, f0: float = 10.0, t0: float = 0.1) -> float:
    """Return a tutorial-style Ricker source sample."""
    arg = math.pi * f0 * (time_value - t0)
    arg2 = arg * arg
    return (1.0 - 2.0 * arg2) * math.exp(-arg2)


def _boundary_markers(mesh: Any) -> tuple[int, ...]:
    """Return sorted exterior boundary markers for a mesh."""
    exterior_facets = getattr(mesh, "exterior_facets", None)
    if exterior_facets is None:
        return ()
    markers = getattr(exterior_facets, "unique_markers", ())
    return tuple(sorted(int(marker) for marker in markers))


def _dg0_family(mesh: Any) -> str:
    """Choose a degree-zero discontinuous family for the mesh cell type."""
    cell = mesh.ufl_cell()
    cell_name_attr = cell.cellname
    cell_name = cell_name_attr() if callable(cell_name_attr) else cell_name_attr
    return "DQ" if cell_name in {"quadrilateral", "hexahedron"} else "DG"


def _partition_boundary_labels(mesh: Any, boundary_labels: Iterable[int]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split labels into interface markers and eligible Clayton markers."""
    labels = tuple(int(lbl) for lbl in boundary_labels)
    outer_markers = _boundary_markers(mesh)
    parent_mesh = getattr(mesh, "_parent_mesh", None) or getattr(mesh, "parent_mesh", None)
    parent_markers = set(_boundary_markers(parent_mesh)) if parent_mesh is not None else set()
    if parent_markers:
        interface_markers = tuple(marker for marker in outer_markers if marker not in parent_markers)
    else:
        interface_markers = ()
    if not interface_markers and outer_markers:
        interface_markers = (max(outer_markers),)
    interface_set = set(interface_markers)
    outer_set = set(outer_markers)
    clayton_labels = tuple(label for label in labels if label in outer_set and label not in interface_set)
    return interface_markers, clayton_labels


def solve_acoustic_submesh(
    mesh: Any,
    source: Any,
    wave_speed: float,
    dt: float,
    t_end: float,
    boundary_labels: Iterable[int],
) -> dict[str, Any]:
    """Run a forward-only acoustic solve and return deterministic diagnostics."""
    if not isinstance(dt, Real) or dt <= 0:
        raise ValueError("dt must be a positive real number.")
    if not isinstance(t_end, Real) or t_end < 0:
        raise ValueError("t_end must be a non-negative real number.")
    if not isinstance(wave_speed, Real) or wave_speed <= 0:
        raise ValueError("wave_speed must be a positive real number.")
    tdim = mesh.topological_dimension() if callable(mesh.topological_dimension) else mesh.topological_dimension
    if int(tdim) != 2:
        raise ValueError(f"Expected a 2D mesh, got topological dimension {tdim}.")

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

    DG0 = FunctionSpace(mesh, _dg0_family(mesh), 0)
    x_parent = SpatialCoordinate(mesh)[0]
    outer_label = 999
    inner_label = 1000
    outer_indicator = Function(DG0).interpolate(conditional(x_parent > 0.5, 1, 0))
    inner_indicator = Function(DG0).interpolate(conditional(x_parent <= 0.5, 1, 0))
    mesh.mark_entities(outer_indicator, outer_label)
    mesh.mark_entities(inner_indicator, inner_label)

    outer_submesh = Submesh(mesh, int(tdim), outer_label)
    inner_submesh = Submesh(mesh, int(tdim), inner_label)
    if outer_submesh.num_cells() <= 0 or inner_submesh.num_cells() <= 0:
        raise ValueError("Both physical and extended submeshes must contain cells.")

    interface_label, clayton_labels = _partition_boundary_labels(outer_submesh, boundary_labels)

    V_outer = FunctionSpace(outer_submesh, "CG", 1)
    V_inner = FunctionSpace(inner_submesh, "CG", 1)
    V = V_outer * V_inner
    u_outer, u_inner = TrialFunctions(V)
    v_outer, v_inner = TestFunctions(V)
    state = Function(V)
    u_outer_prev = Function(V_outer)
    u_inner_prev = Function(V_inner)

    source_term = Constant(float(source)) if isinstance(source, Real) else source
    c = Constant(float(wave_speed))

    dx_outer = Measure("dx", domain=outer_submesh, intersect_measures=(Measure("dx", mesh), Measure("dx", inner_submesh)))
    dx_inner = Measure("dx", domain=inner_submesh, intersect_measures=(Measure("dx", mesh), Measure("dx", outer_submesh)))
    ds_outer = Measure("ds", domain=outer_submesh, intersect_measures=(Measure("ds", inner_submesh),))
    ds_inner = Measure("ds", domain=inner_submesh, intersect_measures=(Measure("ds", outer_submesh),))

    mass_scale = Constant(1.0 / float(dt * dt))
    a_form = (
        mass_scale * inner(u_outer, v_outer) * dx_outer
        + inner(c * c * grad(u_outer), grad(v_outer)) * dx_outer
        + mass_scale * inner(u_inner, v_inner) * dx_inner
        + inner(c * c * grad(u_inner), grad(v_inner)) * dx_inner
        + inner(u_inner, v_outer) * ds_outer(interface_label)
        + inner(u_outer, v_inner) * ds_inner(interface_label)
    )
    clayton_scale = Constant(1.0 / float(dt)) / c
    for label in clayton_labels:
        a_form += clayton_scale * inner(u_outer, v_outer) * ds_outer(label)

    x_inner, y_inner = SpatialCoordinate(inner_submesh)
    source_shape = (1.0 - 2.0 * ((x_inner - 0.5) ** 2 + (y_inner - 0.5) ** 2) / 0.01) * source_term

    interface_bc = EquationBC(
        inner(u_outer - u_inner, v_outer) * ds_outer(interface_label) == inner(Constant(0.0), v_outer) * ds_outer(interface_label),
        state,
        interface_label,
        V=V.sub(0),
    )

    num_steps = max(1, int(math.ceil(float(t_end) / float(dt)))) if t_end > 0 else 1
    for step in range(num_steps):
        time_value = (step + 1) * float(dt)
        ricker_sample = Constant(_ricker_wavelet(time_value))
        l_form = (
            mass_scale * inner(u_outer_prev, v_outer) * dx_outer
            + mass_scale * inner(u_inner_prev, v_inner) * dx_inner
            + ricker_sample * inner(source_shape, v_inner) * dx_inner
        )
        for label in clayton_labels:
            l_form += clayton_scale * inner(u_outer_prev, v_outer) * ds_outer(label)
        solve(a_form == l_form, state, bcs=[interface_bc])
        solved_outer, solved_inner = state.subfunctions
        u_outer_prev.assign(solved_outer)
        u_inner_prev.assign(solved_inner)

    p_outer, p_inner = split(state)
    solution_norm = float(math.sqrt(assemble(inner(p_outer, p_outer) * dx_outer + inner(p_inner, p_inner) * dx_inner)))
    if not math.isfinite(solution_norm):
        raise ValueError("Acoustic solve produced non-finite solution norm.")

    return {
        "mesh": mesh,
        "extended_submesh": outer_submesh,
        "interior_submesh": inner_submesh,
        "source": source,
        "wave_speed": float(wave_speed),
        "dt": float(dt),
        "t_end": float(t_end),
        "boundary_labels": tuple(int(lbl) for lbl in boundary_labels),
        "interface_label": interface_label,
        "clayton_labels": clayton_labels,
        "num_steps": int(num_steps),
        "solution": state,
        "solution_norm": solution_norm,
    }
