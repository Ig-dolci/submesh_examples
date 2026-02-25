"""Acoustic solver entry points."""

from __future__ import annotations

from collections.abc import Iterable
import math
from numbers import Real
from typing import Any

__all__ = [
    "acoustic_solve",
    "solve_acoustic_submesh",
    "evaluate_acoustic_forward_objective",
    "optimize_acoustic_forward_objective",
]


def _normalize_boundary_labels(boundary_labels: Iterable[Any]) -> tuple[Any, ...]:
    """Return boundary labels as a non-empty tuple."""
    if isinstance(boundary_labels, (str, bytes)):
        raise TypeError("boundary_labels must be an iterable of labels, not a string.")
    labels = tuple(boundary_labels)
    if not labels:
        raise ValueError("boundary_labels must contain at least one label.")
    return labels


def _dg0_family(mesh: Any) -> str:
    """Choose the degree-zero discontinuous family for the mesh cell type."""
    cell = mesh.ufl_cell()
    cell_name_attr = cell.cellname
    cell_name = cell_name_attr() if callable(cell_name_attr) else cell_name_attr
    if cell_name in {"quadrilateral", "hexahedron"}:
        return "DQ"
    return "DG"


def _mesh_topological_dimension(mesh: Any) -> int:
    """Read mesh topological dimension from callable or attribute APIs."""
    tdim_attr = mesh.topological_dimension
    return int(tdim_attr() if callable(tdim_attr) else tdim_attr)


def _build_extended_domain_submesh(mesh: Any, label_value: int = 999) -> tuple[Any, int]:
    """Mark x > 0.5 cells and build the labeled extended-domain submesh."""
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
    """Convert scalar source inputs to Firedrake constants."""
    from firedrake import Constant

    if isinstance(source, Real):
        return Constant(float(source))
    return source


def _coerce_wave_speed_pair(wave_speed: Any) -> tuple[Any, Any]:
    """Return a pair of wave-speed coefficients for outer and inner domains."""
    from firedrake import Constant

    if isinstance(wave_speed, Real):
        c = Constant(float(wave_speed))
        return c, c
    return wave_speed, wave_speed


def _normalize_source_collection(source: Any) -> tuple[Any, ...]:
    """Normalize scalar or iterable source inputs to a non-empty tuple."""
    if isinstance(source, Iterable) and not isinstance(source, (str, bytes)):
        sources = tuple(source)
        if not sources:
            raise ValueError("source iterable must contain at least one entry.")
        return sources
    return (source,)


def _normalize_observed_solution_norm(
    observed_solution_norm: Any,
    source_count: int,
) -> tuple[float, ...]:
    """Normalize one or many observed norms to one value per source."""
    if isinstance(observed_solution_norm, Real):
        values = (float(observed_solution_norm),)
    elif isinstance(observed_solution_norm, Iterable) and not isinstance(observed_solution_norm, (str, bytes)):
        values = tuple(float(value) for value in observed_solution_norm)
        if not values:
            raise ValueError("observed_solution_norm iterable must contain at least one value.")
    else:
        raise TypeError("observed_solution_norm must be a real number or iterable of real numbers.")

    if any(not math.isfinite(value) for value in values):
        raise ValueError("observed_solution_norm values must be finite.")

    if len(values) == 1 and source_count > 1:
        values = values * source_count
    if len(values) != source_count:
        raise ValueError(
            "observed_solution_norm must provide one value per source or a single shared value."
        )
    return values


def acoustic_solve(
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
        Positive time-step size used by the implicit update; set ``dt == t_end`` for a
        one-step solve.
    t_end : float
        Non-negative final simulation time used with ``dt`` to compute
        ``num_steps = max(1, ceil(t_end / dt))``.
    boundary_labels : Iterable[object]
        Candidate exterior boundary labels on the extended-domain submesh. Labels inferred as
        the interface boundary are reserved for coupling, while the remaining labels are used
        for Clayton A1 damping.

    Returns
    -------
    dict[str, object]
        Solver state and metadata, including diagnostics ``solution_norm``,
        ``interface_label``, and ``clayton_labels``.
    """
    if not isinstance(dt, Real) or dt <= 0:
        raise ValueError("dt must be a positive real number.")
    if not isinstance(t_end, Real) or t_end < 0:
        raise ValueError("t_end must be a non-negative real number.")
    if isinstance(wave_speed, Real) and wave_speed <= 0:
        raise ValueError("wave_speed must be positive when provided as a scalar.")
    mesh_topological_dimension = _mesh_topological_dimension(mesh)
    if mesh_topological_dimension != 2:
        raise ValueError(
            "mesh.topological_dimension() must be 2 for acoustic_solve; "
            f"got {mesh_topological_dimension}."
        )

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
        VTKFile,
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

    outer_markers = tuple(sorted(int(marker) for marker in extended_submesh.exterior_facets.unique_markers))
    parent_boundary_markers = {int(marker) for marker in mesh.exterior_facets.unique_markers}
    if not outer_markers:
        raise ValueError("Extended-domain Submesh must expose boundary labels.")
    interface_markers = tuple(marker for marker in outer_markers if marker not in parent_boundary_markers)
    if not interface_markers:
        raise ValueError("Extended-domain Submesh must expose at least one interface boundary label.")

    interface_marker_set = set(interface_markers)
    outer_non_interface_markers = set(outer_markers) - interface_marker_set
    clayton_labels = tuple(label for label in labels if label in outer_non_interface_markers)
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

    outfile = VTKFile("acoustic_submesh_solution.pvd")
    for step in range(num_steps):
        solve(a == L, state, bcs=[interface_bc])
        solved_outer, solved_inner = state.subfunctions
        u_outer_prev.assign(solved_outer)
        u_inner_prev.assign(solved_inner)
        if step % 10 == 0:
            print(f"  Completed step {step + 1} / {num_steps}")
            outfile.write(solved_outer)

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


def solve_acoustic_submesh(
    mesh: Any,
    source: Any,
    wave_speed: Any,
    dt: float,
    t_end: float,
    boundary_labels: Iterable[Any],
) -> dict[str, Any]:
    """Backward-compatible wrapper around :func:`acoustic_solve`."""
    return acoustic_solve(
        mesh=mesh,
        source=source,
        wave_speed=wave_speed,
        dt=dt,
        t_end=t_end,
        boundary_labels=boundary_labels,
    )


def evaluate_acoustic_forward_objective(
    mesh: Any,
    source: Any,
    wave_speed: float,
    dt: float,
    t_end: float,
    boundary_labels: Iterable[Any],
    observed_solution_norm: Any,
) -> dict[str, Any]:
    """Evaluate a forward-style least-squares objective from one or more source solves."""
    if not isinstance(wave_speed, Real) or wave_speed <= 0:
        raise ValueError("wave_speed must be a positive real number.")

    sources = _normalize_source_collection(source)
    observed_norms = _normalize_observed_solution_norm(observed_solution_norm, len(sources))
    labels = _normalize_boundary_labels(boundary_labels)

    objective = 0.0
    residuals: list[float] = []
    forward_results: list[dict[str, Any]] = []
    for source_term, observed_norm in zip(sources, observed_norms):
        forward_result = solve_acoustic_submesh(
            mesh=mesh,
            source=source_term,
            wave_speed=float(wave_speed),
            dt=dt,
            t_end=t_end,
            boundary_labels=labels,
        )
        residual = float(forward_result["solution_norm"]) - observed_norm
        objective += 0.5 * residual * residual
        residuals.append(float(residual))
        forward_results.append(forward_result)

    return {
        "mesh": mesh,
        "source": sources if len(sources) > 1 else sources[0],
        "wave_speed": float(wave_speed),
        "dt": float(dt),
        "t_end": float(t_end),
        "boundary_labels": tuple(labels),
        "observed_solution_norm": tuple(observed_norms),
        "residuals": tuple(residuals),
        "objective": float(objective),
        "forward_results": tuple(forward_results),
    }


def optimize_acoustic_forward_objective(
    mesh: Any,
    source: Any,
    initial_wave_speed: float,
    dt: float,
    t_end: float,
    boundary_labels: Iterable[Any],
    observed_solution_norm: Any,
    *,
    learning_rate: float = 0.5,
    max_iter: int = 20,
    ftol: float = 1e-3,
    objective_tol: float = 1e-8,
    fd_step: float = 1e-2,
    min_wave_speed: float = 1e-6,
    max_backtracking_steps: int = 6,
) -> dict[str, Any]:
    """Run a forward objective optimization loop using finite-difference updates."""
    if not isinstance(initial_wave_speed, Real) or initial_wave_speed <= 0:
        raise ValueError("initial_wave_speed must be a positive real number.")
    if not isinstance(learning_rate, Real) or learning_rate <= 0:
        raise ValueError("learning_rate must be a positive real number.")
    if not isinstance(fd_step, Real) or fd_step <= 0:
        raise ValueError("fd_step must be a positive real number.")
    if not isinstance(min_wave_speed, Real) or min_wave_speed <= 0:
        raise ValueError("min_wave_speed must be a positive real number.")
    if not isinstance(max_iter, int) or max_iter <= 0:
        raise ValueError("max_iter must be a positive integer.")
    if not isinstance(max_backtracking_steps, int) or max_backtracking_steps < 0:
        raise ValueError("max_backtracking_steps must be a non-negative integer.")
    if not isinstance(ftol, Real) or ftol < 0:
        raise ValueError("ftol must be a non-negative real number.")
    if not isinstance(objective_tol, Real) or objective_tol < 0:
        raise ValueError("objective_tol must be a non-negative real number.")

    sources = _normalize_source_collection(source)
    observed_norms = _normalize_observed_solution_norm(observed_solution_norm, len(sources))
    labels = _normalize_boundary_labels(boundary_labels)

    wave_speed = max(float(initial_wave_speed), float(min_wave_speed))
    current_eval = evaluate_acoustic_forward_objective(
        mesh=mesh,
        source=sources,
        wave_speed=wave_speed,
        dt=dt,
        t_end=t_end,
        boundary_labels=labels,
        observed_solution_norm=observed_norms,
    )
    objective_history = [float(current_eval["objective"])]
    wave_speed_history = [float(wave_speed)]
    stop_reason = "max_iter"

    if objective_history[-1] <= objective_tol:
        stop_reason = "objective_tol"
    else:
        for _ in range(max_iter):
            speed_plus = wave_speed + float(fd_step)
            speed_minus = max(float(min_wave_speed), wave_speed - float(fd_step))

            plus_eval = evaluate_acoustic_forward_objective(
                mesh=mesh,
                source=sources,
                wave_speed=speed_plus,
                dt=dt,
                t_end=t_end,
                boundary_labels=labels,
                observed_solution_norm=observed_norms,
            )
            minus_eval = evaluate_acoustic_forward_objective(
                mesh=mesh,
                source=sources,
                wave_speed=speed_minus,
                dt=dt,
                t_end=t_end,
                boundary_labels=labels,
                observed_solution_norm=observed_norms,
            )

            denom = speed_plus - speed_minus
            gradient = 0.0 if denom == 0 else (plus_eval["objective"] - minus_eval["objective"]) / denom

            step_scale = float(learning_rate)
            previous_objective = float(current_eval["objective"])
            candidate_eval = current_eval
            candidate_wave_speed = wave_speed

            for _ in range(max_backtracking_steps + 1):
                trial_wave_speed = max(float(min_wave_speed), wave_speed - step_scale * float(gradient))
                trial_eval = evaluate_acoustic_forward_objective(
                    mesh=mesh,
                    source=sources,
                    wave_speed=trial_wave_speed,
                    dt=dt,
                    t_end=t_end,
                    boundary_labels=labels,
                    observed_solution_norm=observed_norms,
                )
                candidate_eval = trial_eval
                candidate_wave_speed = trial_wave_speed
                if trial_eval["objective"] <= previous_objective:
                    break
                step_scale *= 0.5

            current_eval = candidate_eval
            wave_speed = float(candidate_wave_speed)
            objective_history.append(float(current_eval["objective"]))
            wave_speed_history.append(float(wave_speed))

            if objective_history[-1] <= objective_tol:
                stop_reason = "objective_tol"
                break

            relative_change = abs(previous_objective - objective_history[-1]) / max(abs(previous_objective), 1.0)
            if relative_change <= ftol:
                stop_reason = "ftol"
                break

    return {
        "mesh": mesh,
        "source": sources if len(sources) > 1 else sources[0],
        "dt": float(dt),
        "t_end": float(t_end),
        "boundary_labels": tuple(labels),
        "observed_solution_norm": tuple(observed_norms),
        "objective_history": tuple(objective_history),
        "wave_speed_history": tuple(wave_speed_history),
        "final_wave_speed": float(wave_speed_history[-1]),
        "final_objective": float(objective_history[-1]),
        "num_iterations": len(objective_history) - 1,
        "stop_reason": stop_reason,
        "forward_results": current_eval["forward_results"],
    }


if __name__ == "__main__":
    import firedrake

    mesh = firedrake.RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True)
    result = acoustic_solve(
        mesh=mesh,
        source=1.0,
        wave_speed=1.0,
        dt=0.01,
        t_end=1.0,
        boundary_labels=(1, 2, 3, 4),
    )
    print(f"Acoustic submesh solve completed with solution norm: {result['solution_norm']:.6e}")
