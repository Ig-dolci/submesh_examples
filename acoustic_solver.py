"""Acoustic solver entry points."""

from __future__ import annotations

from collections.abc import Iterable
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


def _build_extended_domain_submesh(mesh: Any, label_value: int = 999) -> tuple[Any, int]:
    from firedrake import Function, FunctionSpace, SpatialCoordinate, Submesh, conditional

    DG0 = FunctionSpace(mesh, _dg0_family(mesh), 0)
    indicator_function = Function(DG0)
    x = SpatialCoordinate(mesh)[0]
    indicator_function.interpolate(conditional(x > 0.5, 1, 0))
    mesh.mark_entities(indicator_function, label_value)
    submesh = Submesh(mesh, mesh.topological_dimension, label_value)
    if submesh.num_cells() <= 0:
        raise ValueError("Extended-domain Submesh must contain at least one cell.")
    return submesh, label_value


def solve_acoustic_submesh(
    mesh: Any,
    source: Any,
    wave_speed: Any,
    dt: float,
    t_end: float,
    boundary_labels: Iterable[Any],
) -> dict[str, Any]:
    """Solve an acoustic submesh model with labeled boundary conditions.

    Parameters
    ----------
    mesh : object
        Parent Firedrake mesh that defines the physical computational domain.
    source : object
        Source term for the acoustic wave equation (for example a function or expression).
    wave_speed : float or object
        Acoustic wave speed coefficient; scalars must be strictly positive.
    dt : float
        Time-step size used by the time integrator.
    t_end : float
        Final simulation time.
    boundary_labels : Iterable[object]
        Boundary marker labels where acoustic boundary conditions are applied.

    Returns
    -------
    dict[str, object]
        Normalized input data for downstream submesh assembly and solve steps,
        including a DG0-labeled extended-domain submesh.
    """
    if not isinstance(dt, Real) or dt <= 0:
        raise ValueError("dt must be a positive real number.")
    if not isinstance(t_end, Real) or t_end < 0:
        raise ValueError("t_end must be a non-negative real number.")
    if isinstance(wave_speed, Real) and wave_speed <= 0:
        raise ValueError("wave_speed must be positive when provided as a scalar.")

    labels = _normalize_boundary_labels(boundary_labels)
    extended_submesh, extended_domain_label = _build_extended_domain_submesh(mesh)
    return {
        "mesh": mesh,
        "extended_submesh": extended_submesh,
        "extended_domain_label": extended_domain_label,
        "source": source,
        "wave_speed": wave_speed,
        "dt": float(dt),
        "t_end": float(t_end),
        "boundary_labels": labels,
    }
