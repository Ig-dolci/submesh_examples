"""Run a 2D acoustic simulation with HABC submesh coupling.

The model solves the wave equation on a parent mesh and augments
boundary behavior with one-way equations on three boundary submeshes
(left, right, and top). The submesh solutions are blended back into
the parent field every time step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import firedrake as fd
import finat
import numpy as np


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for the HABC simulation."""

    ensemble_size: int = 1
    dt: float = 0.001
    final_time: float = 1.0
    nx: int = 80
    ny: int = 80
    domain_length: float = 1.5
    boundary_distance: float = 0.2
    frequency_peak: float = 7.0
    source_locations: tuple[tuple[float, float], ...] = ((0.75, 0.75),)
    progress_interval: int = 100
    left_marker: int = 999
    right_marker: int = 998
    bottom_marker: int = 997

    @property
    def total_steps(self) -> int:
        """Return the number of explicit time steps."""
        return int(self.final_time / self.dt) + 1


def ricker_wavelet(
    time: float,
    peak_frequency: float,
    amplitude: float = 1.0,
) -> float:
    """Evaluate a Ricker wavelet at a given time."""
    ts = 1.5
    shifted_time = time - ts * np.sqrt(6.0) / (np.pi * peak_frequency)
    omega = 2.0 * np.pi * peak_frequency
    omega_squared = omega * omega
    factor = 1.0 - 0.5 * omega_squared * shifted_time * shifted_time
    return amplitude * factor * np.exp(
        -0.25 * omega_squared * shifted_time * shifted_time
    )


def get_interface_markers(
    parent_mesh: Any,
    child_mesh: Any,
) -> tuple[int, ...]:
    """Return markers present on a child submesh only.

    Markers shared with the parent mesh exterior are excluded.
    """
    parent_exterior = {
        int(marker)
        for marker in parent_mesh.exterior_facets.unique_markers
    }
    child_exterior = {
        int(marker)
        for marker in child_mesh.exterior_facets.unique_markers
    }
    return tuple(sorted(child_exterior - parent_exterior))


def mark_submesh(
    mesh: Any,
    dq0: fd.FunctionSpace,
    indicator_expr: Any,
    marker: int,
) -> Any:
    """Mark cells from an indicator expression and create a submesh."""
    indicator = fd.Function(dq0).interpolate(
        fd.conditional(indicator_expr, 1, 0)
    )
    mesh.mark_entities(indicator, marker)
    return fd.Submesh(mesh, 2, marker)


def create_submeshes(
    mesh: Any,
    boundary_distance: fd.Constant,
    domain_length: float,
    markers: tuple[int, int, int],
) -> tuple[Any, Any, Any, fd.Measure]:
    """Create left/right/top boundary submeshes and intersected measure."""
    left_marker, right_marker, bottom_marker = markers
    x, z = fd.SpatialCoordinate(mesh)
    distance_left = x
    distance_right = domain_length - x
    distance_top = domain_length - z

    dq0 = fd.FunctionSpace(mesh, "DG", 0)
    submesh_left = mark_submesh(
        mesh,
        dq0,
        distance_left < boundary_distance,
        left_marker,
    )
    submesh_right = mark_submesh(
        mesh,
        dq0,
        distance_right < boundary_distance,
        right_marker,
    )
    submesh_bottom = mark_submesh(
        mesh,
        dq0,
        fd.And(
            distance_top < boundary_distance,
            fd.And(
                distance_left > boundary_distance,
                distance_right > boundary_distance,
            ),
        ),
        bottom_marker,
    )

    dx0 = fd.Measure(
        "dx",
        domain=mesh,
        intersect_measures=(
            fd.Measure("dx", submesh_left),
            fd.Measure("dx", submesh_right),
            fd.Measure("dx", submesh_bottom),
        ),
    )
    return submesh_left, submesh_right, submesh_bottom, dx0


def build_source_term(
    mesh: Any,
    parent_space: fd.FunctionSpace,
    source_location: tuple[float, float],
) -> fd.Cofunction:
    """Project a point source to the dual of the parent function space."""
    source_mesh = fd.VertexOnlyMesh(mesh, [source_location])
    source_space = fd.FunctionSpace(source_mesh, "DG", 0)
    source_density = fd.Function(source_space).interpolate(1.0)
    source_cofunction = fd.assemble(
        source_density * fd.TestFunction(source_space) * fd.dx
    )
    return fd.Cofunction(parent_space.dual()).interpolate(source_cofunction)


def build_transition_weights(
    submesh_left: Any,
    submesh_right: Any,
    submesh_bottom: Any,
    left_space: fd.FunctionSpace,
    right_space: fd.FunctionSpace,
    bottom_space: fd.FunctionSpace,
    domain_length: float,
    transition_width: fd.Constant,
) -> list[fd.Function]:
    """Construct linear blending weights over each absorbing submesh."""
    x_left, _ = fd.SpatialCoordinate(submesh_left)
    x_right, _ = fd.SpatialCoordinate(submesh_right)
    _, z_bottom = fd.SpatialCoordinate(submesh_bottom)

    distance_left = x_left
    distance_right = domain_length - x_right
    distance_top = domain_length - z_bottom

    weight_left_expr = fd.conditional(
        distance_left < transition_width,
        (transition_width - distance_left) / transition_width,
        0.0,
    )
    weight_right_expr = fd.conditional(
        distance_right < transition_width,
        (transition_width - distance_right) / transition_width,
        0.0,
    )
    weight_bottom_expr = fd.conditional(
        distance_top < transition_width,
        (transition_width - distance_top) / transition_width,
        0.0,
    )

    return [
        fd.Function(left_space).interpolate(weight_left_expr),
        fd.Function(right_space).interpolate(weight_right_expr),
        fd.Function(bottom_space).interpolate(weight_bottom_expr),
    ]


def wave_equation_solver(
    c: fd.Function,
    source_function: fd.Cofunction,
    dt: float,
    mixed_space: fd.FunctionSpace,
    dx0: fd.Measure,
    quad_rule0: Any,
) -> tuple[
    fd.LinearVariationalSolver,
    fd.Function,
    fd.Function,
    fd.Function,
    tuple[fd.Function, ...],
]:
    """Build and return the linear variational solver for one wave step."""
    u = fd.TrialFunction(mixed_space)
    v = fd.TestFunction(mixed_space)
    u_components = fd.split(u)
    v_components = fd.split(v)
    u0 = u_components[0]
    v0 = v_components[0]

    u_n = fd.Function(mixed_space)
    u_nm1 = fd.Function(mixed_space)
    u_np1 = fd.Function(mixed_space)
    u_n_components = u_n.subfunctions
    u_nm1_components = u_nm1.subfunctions
    u_n0 = u_n_components[0]
    u_nm10 = u_nm1_components[0]

    subspaces = [mixed_space.sub(1), mixed_space.sub(2), mixed_space.sub(3)]
    mesh = mixed_space.sub(0).mesh()
    submeshes = [space.mesh() for space in subspaces]
    c_subspaces = [
        fd.Function(space).interpolate(c, allow_missing_dofs=True)
        for space in subspaces
    ]
    u_n0_subspaces = [
        fd.Function(space).interpolate(u_n0, allow_missing_dofs=True)
        for space in subspaces
    ]

    m = 1 / (c * c)
    dt_const = fd.Constant(dt)
    dt2_const = fd.Constant(dt**2)
    dx0_rule = dx0(scheme=quad_rule0) if quad_rule0 is not None else dx0
    wave_form = (
        m * (u0 - 2.0 * u_n0 + u_nm10) / dt2_const * v0 * dx0_rule
        + fd.dot(fd.grad(u0), fd.grad(v0)) * dx0_rule
    )

    bcs = []
    direction_data = [(-1.0, 0), (1.0, 0), (1.0, 1)]
    for idx, (
        space,
        submesh,
        c_sub,
        (direction_sign, direction_axis),
    ) in enumerate(
        zip(subspaces, submeshes, c_subspaces, direction_data),
        start=1,
    ):
        u_i = u_components[idx]
        v_i = v_components[idx]
        u_n_i = u_n_components[idx]

        dx_i = fd.Measure(
            "dx",
            domain=submesh,
            intersect_measures=(fd.Measure("dx", mesh),),
        )
        ds_i_int = fd.Measure(
            "ds",
            domain=submesh,
            intersect_measures=(fd.Measure("dS", mesh),),
        )

        wave_form += (
            (1 / c_sub) * (u_i - u_n_i) / dt_const * v_i * dx_i
            + direction_sign * u_i.dx(direction_axis) * v_i * dx_i
        )

        interface_markers = get_interface_markers(mesh, submesh)
        if not interface_markers:
            raise ValueError(
                "No interface markers found between parent mesh and "
                f"submesh_{idx}"
            )

        interface_eq = (
            fd.inner(u_i - u0("+"), v_i) * ds_i_int(interface_markers)
            == fd.inner(fd.Constant(0.0), v_i) * ds_i_int(interface_markers)
        )
        bcs.append(
            fd.EquationBC(interface_eq, u_np1, interface_markers, V=space)
        )

    problem = fd.LinearVariationalProblem(
        fd.lhs(wave_form),
        fd.rhs(wave_form) + source_function,
        u_np1,
        bcs=bcs,
    )
    solver_parameters = {
        "mat_type": "matfree",
        "ksp_type": "gmres",
        "pc_type": "bjacobi",
        "ksp_rtol": 1.0e-8,
    }
    solver = fd.LinearVariationalSolver(
        problem,
        solver_parameters=solver_parameters,
    )
    return solver, u_np1, u_n, u_nm1, tuple(u_n0_subspaces)


def apply_habc_blending(
    parent_component: fd.Function,
    submesh_components: list[fd.Function],
    submesh_weights: list[fd.Function],
    mesh_weights: list[fd.Function],
    weighted_sums: list[fd.Function],
) -> None:
    """Blend submesh updates back into the parent solution component."""
    for weight_sub, u_sub, weighted_sum, weight_mesh in zip(
        submesh_weights,
        submesh_components,
        weighted_sums,
        mesh_weights,
    ):
        weighted_sum.interpolate(weight_sub * u_sub, allow_missing_dofs=True)
        weight_mesh.interpolate(weight_sub, allow_missing_dofs=True)
        parent_component.interpolate(
            (1.0 - weight_mesh) * parent_component + weighted_sum
        )


def main(config: SimulationConfig | None = None) -> None:
    """Run the simulation and write the final pressure field to disk."""
    simulation = config or SimulationConfig()
    ensemble = fd.Ensemble(fd.COMM_WORLD, simulation.ensemble_size)
    source_rank = ensemble.ensemble_comm.rank

    source_locations = np.asarray(simulation.source_locations, dtype=float)
    if source_rank >= len(source_locations):
        raise ValueError(
            "Not enough source locations for ensemble ranks: "
            f"rank={source_rank}, locations={len(source_locations)}"
        )

    boundary_distance = fd.Constant(simulation.boundary_distance)
    mesh = fd.SquareMesh(
        simulation.nx,
        simulation.ny,
        simulation.domain_length,
        comm=ensemble.comm,
    )
    submesh_left, submesh_right, submesh_bottom, dx0 = create_submeshes(
        mesh,
        boundary_distance,
        simulation.domain_length,
        (
            simulation.left_marker,
            simulation.right_marker,
            simulation.bottom_marker,
        ),
    )

    parent_space = fd.FunctionSpace(mesh, "KMV", 1)
    left_space = fd.FunctionSpace(submesh_left, "KMV", 1)
    right_space = fd.FunctionSpace(submesh_right, "KMV", 1)
    bottom_space = fd.FunctionSpace(submesh_bottom, "KMV", 1)
    mixed_space = parent_space * left_space * right_space * bottom_space

    quad_rule0 = finat.quadrature.make_quadrature(
        parent_space.finat_element.cell,
        parent_space.ufl_element().degree(),
        "KMV",
    )
    velocity = fd.Function(parent_space).interpolate(2.0)

    source_term = build_source_term(
        mesh,
        parent_space,
        tuple(source_locations[source_rank]),
    )
    rhs_term = fd.Cofunction(mixed_space.dual())
    solver, u_np1, u_n, u_nm1, u_n0_subspaces = wave_equation_solver(
        velocity,
        rhs_term,
        simulation.dt,
        mixed_space,
        dx0,
        quad_rule0,
    )

    u_n0 = u_n.subfunctions[0]
    parent_next = u_np1.subfunctions[0]
    submesh_components = [
        u_np1.subfunctions[1],
        u_np1.subfunctions[2],
        u_np1.subfunctions[3],
    ]

    submesh_weights = build_transition_weights(
        submesh_left,
        submesh_right,
        submesh_bottom,
        left_space,
        right_space,
        bottom_space,
        simulation.domain_length,
        boundary_distance,
    )
    mesh_weights = [fd.Function(parent_space) for _ in submesh_weights]
    weighted_sums = [fd.Function(parent_space) for _ in submesh_weights]

    for step in range(simulation.total_steps):
        time = step * simulation.dt
        source_value = ricker_wavelet(time, simulation.frequency_peak)
        rhs_term.sub(0).assign(source_value * source_term)

        for u_n0_sub in u_n0_subspaces:
            u_n0_sub.interpolate(u_n0, allow_missing_dofs=True)

        solver.solve()
        apply_habc_blending(
            parent_component=parent_next,
            submesh_components=submesh_components,
            submesh_weights=submesh_weights,
            mesh_weights=mesh_weights,
            weighted_sums=weighted_sums,
        )

        u_nm1.assign(u_n)
        u_n.assign(u_np1)

        if step % simulation.progress_interval == 0:
            print(f"Step {step}/{simulation.total_steps}, time={time:.3f}")

    fd.VTKFile("solution.pvd").write(u_np1.sub(0))


if __name__ == "__main__":
    main()
