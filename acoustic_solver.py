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
        Normalized input data for downstream submesh assembly and solve steps.
    """
    if not isinstance(dt, Real) or dt <= 0:
        raise ValueError("dt must be a positive real number.")
    if not isinstance(t_end, Real) or t_end < 0:
        raise ValueError("t_end must be a non-negative real number.")
    if isinstance(wave_speed, Real) and wave_speed <= 0:
        raise ValueError("wave_speed must be positive when provided as a scalar.")

    labels = _normalize_boundary_labels(boundary_labels)
    return {
        "mesh": mesh,
        "source": source,
        "wave_speed": wave_speed,
        "dt": float(dt),
        "t_end": float(t_end),
        "boundary_labels": labels,
    }
