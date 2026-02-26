"""Forward acoustic solver utilities."""

from __future__ import annotations

import math
from typing import Any


def solve_acoustic_submesh(
    *,
    dt: float,
    final_time: float,
    mesh: Any | None = None,
    physical_cell_label: int = 100,
    extended_cell_label: int = 101,
    outer_boundary_labels: tuple[int, ...] = (1, 2, 3, 4),
    interface_labels: tuple[int, ...] | None = None,
    frequency_peak: float = 1.0,
    source_amplitude: float = 1.0,
    source_x: float = 0.5,
    source_y: float = 0.5,
    c: float = 1.0,
) -> dict[str, Any]:
    """Run a forward-only acoustic time march and return simulation data.

    Parameters
    ----------
    dt:
        Time increment per step.
    final_time:
        End time of the simulation.
    mesh:
        Optional parent mesh used to build physical/extended submeshes.
    physical_cell_label, extended_cell_label:
        Cell labels used to extract physical and extended Submesh domains.
    outer_boundary_labels:
        Parent boundary labels eligible for absorbing treatment.
    interface_labels:
        Interface labels between physical/extended domains. These are removed
        from absorbing-boundary treatment.
    frequency_peak:
        Peak frequency for the Ricker wavelet forcing.
    source_amplitude:
        Amplitude multiplier for the source term.
    source_x, source_y:
        Source location metadata retained in the returned payload.
    c:
        Wave speed used in the simple scalar update.

    Returns
    -------
    dict
        A dictionary with the following keys:
        - ``time_values``: list of simulation times (including t=0).
        - ``source_values``: list of Ricker source values at each time.
        - ``pressure_trace``: list of forward pressure values per time step.
        - ``final_pressure``: final pressure scalar.
        - ``parameters``: normalized input parameters used for the run.
        - ``domain``: submesh metadata including interface and absorbing labels.
    """
    if dt <= 0.0:
        raise ValueError("dt must be positive")
    if final_time < 0.0:
        raise ValueError("final_time must be non-negative")
    if frequency_peak <= 0.0:
        raise ValueError("frequency_peak must be positive")
    if not outer_boundary_labels:
        raise ValueError("outer_boundary_labels must be non-empty")

    steps = int(round(final_time / dt))
    time_values = [n * dt for n in range(steps + 1)]
    inferred_interface_labels = set(interface_labels or ())
    if not inferred_interface_labels:
        inferred_interface_labels.add(max(outer_boundary_labels) + 1)
    absorbing_boundary_labels = tuple(
        label for label in outer_boundary_labels if label not in inferred_interface_labels
    )
    absorbing_term_enabled = bool(absorbing_boundary_labels)
    clayton_a1_scale = c * float(len(absorbing_boundary_labels))

    physical_mesh = None
    extended_mesh = None
    if mesh is not None:
        from firedrake import Submesh

        dim = mesh.topological_dimension
        physical_mesh = Submesh(mesh, dim, physical_cell_label, name="physical_mesh")
        extended_mesh = Submesh(mesh, dim, extended_cell_label, name="extended_mesh")

    pressure_prev = 0.0
    pressure_curr = 0.0
    source_values: list[float] = []
    pressure_trace: list[float] = [pressure_curr]
    absorbing_contribution_trace: list[float] = [0.0]
    t0 = 1.5 / frequency_peak

    for t in time_values[1:]:
        arg = math.pi * frequency_peak * (t - t0)
        ricker = source_amplitude * (1.0 - 2.0 * arg * arg) * math.exp(-(arg * arg))
        source_values.append(ricker)
        boundary_contribution = (
            dt * clayton_a1_scale * (pressure_curr - pressure_prev) if absorbing_term_enabled else 0.0
        )
        pressure_next = 2.0 * pressure_curr - pressure_prev + (dt * c) ** 2 * ricker - boundary_contribution
        pressure_prev, pressure_curr = pressure_curr, pressure_next
        pressure_trace.append(pressure_curr)
        absorbing_contribution_trace.append(boundary_contribution)

    if not source_values:
        source_values = [0.0]

    return {
        "time_values": time_values,
        "source_values": source_values,
        "pressure_trace": pressure_trace,
        "absorbing_contribution_trace": absorbing_contribution_trace,
        "final_pressure": pressure_curr,
        "domain": {
            "physical_mesh": physical_mesh,
            "extended_mesh": extended_mesh,
            "interface_labels": tuple(sorted(inferred_interface_labels)),
            "outer_boundary_labels": outer_boundary_labels,
            "absorbing_boundary_labels": absorbing_boundary_labels,
            "absorbing_term_enabled": absorbing_term_enabled,
        },
        "parameters": {
            "dt": dt,
            "final_time": final_time,
            "physical_cell_label": physical_cell_label,
            "extended_cell_label": extended_cell_label,
            "outer_boundary_labels": outer_boundary_labels,
            "interface_labels": tuple(sorted(inferred_interface_labels)),
            "frequency_peak": frequency_peak,
            "source_amplitude": source_amplitude,
            "source_location": (source_x, source_y),
            "c": c,
        },
    }
