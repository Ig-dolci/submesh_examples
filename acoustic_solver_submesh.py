import os
import shutil
from dataclasses import dataclass

import finat
import numpy as np
from firedrake import *
from firedrake.adjoint import *


@dataclass(frozen=True)
class DivergenceConfig:
    check_every: int = 5
    growth_factor: float = 50.0
    abs_limit: float = 1.0e6


def ricker_wavelet(t, fs, amp=1.0):
    ts = 1.5
    t0 = t - ts * np.sqrt(6.0) / (np.pi * fs)
    omega2 = (2.0 * np.pi * fs) * (2.0 * np.pi * fs)
    return amp * (1.0 - 0.5 * omega2 * t0 * t0) * np.exp(-0.25 * omega2 * t0 * t0)


def get_interface_markers(parent_mesh, child_mesh):
    parent_exterior = {int(marker) for marker in parent_mesh.exterior_facets.unique_markers}
    child_exterior = {int(marker) for marker in child_mesh.exterior_facets.unique_markers}
    return tuple(sorted(child_exterior - parent_exterior))


def get_shared_exterior_markers(parent_mesh, child_mesh):
    parent_exterior = {int(marker) for marker in parent_mesh.exterior_facets.unique_markers}
    child_exterior = tuple(int(marker) for marker in child_mesh.exterior_facets.unique_markers)
    return tuple(marker for marker in child_exterior if marker in parent_exterior)


def cleanup_outputs(*output_files, output_dir=None):
    for output_file in output_files:
        if os.path.exists(output_file):
            os.remove(output_file)
    if output_dir and os.path.isdir(output_dir):
        shutil.rmtree(output_dir)


def mark_submesh(mesh, dq0, indicator_expr, marker):
    indicator = Function(dq0).interpolate(conditional(indicator_expr, 1, 0))
    mesh.mark_entities(indicator, marker)
    return Submesh(mesh, 2, marker)


def check_divergence(
    solution,
    step,
    previous_norm,
    growth_factor,
    abs_limit,
):
    current_norm = norm(solution)
    current_max_abs = float(np.max(np.abs(solution.dat.data_ro)))

    if not np.isfinite(current_norm) or not np.isfinite(current_max_abs):
        raise RuntimeError(
            f"Divergence detected at step {step}: non-finite solution values "
            f"(norm={current_norm}, max_abs={current_max_abs})."
        )

    if current_max_abs > abs_limit:
        raise RuntimeError(
            f"Divergence detected at step {step}: max_abs={current_max_abs} "
            f"exceeds limit {abs_limit}."
        )

    if previous_norm is not None:
        reference_norm = max(previous_norm, 1.0e-12)
        if current_norm > growth_factor * reference_norm:
            raise RuntimeError(
                f"Divergence detected at step {step}: norm jumped from "
                f"{previous_norm} to {current_norm}."
            )

    return current_norm


def wave_equation_solver(c, source_function, dt, V, dx0, quad_rule0):
    u = TrialFunction(V)
    v = TestFunction(V)
    u_components = split(u)
    v_components = split(v)
    u0 = u_components[0]
    v0 = v_components[0]

    u_n = Function(V)
    u_nm1 = Function(V)
    u_np1 = Function(V)
    u_n_components = u_n.subfunctions
    u_nm1_components = u_nm1.subfunctions
    u_n0 = u_n_components[0]
    u_nm10 = u_nm1_components[0]

    subspaces = [V.sub(1), V.sub(2), V.sub(3)]
    mesh = V.sub(0).mesh()
    submeshes = [space.mesh() for space in subspaces]
    c_subspaces = [
        Function(space).interpolate(c, allow_missing_dofs=True)
        for space in subspaces
    ]
    u_n0_subspaces = [
        Function(space).interpolate(u_n0, allow_missing_dofs=True)
        for space in subspaces
    ]

    m = 1 / (c * c)
    time_term = m * (u0 - 2.0 * u_n0 + u_nm10) / Constant(dt**2) * v0 * dx0(scheme=quad_rule0)
    a = dot(grad(u_n0), grad(v0)) * dx0(scheme=quad_rule0)
    F = a + time_term

    sign_factors = (1.0, -1.0, -1.0)
    bcs = []
    for idx, (space, submesh, c_sub, sign) in enumerate(
        zip(subspaces, submeshes, c_subspaces, sign_factors),
        start=1,
    ):
        ds_ext = Measure("ds", domain=submesh, intersect_measures=(Measure("ds", mesh),))
        u_sub = Function(space).interpolate(u_n0, allow_missing_dofs=True)
        interface_markers = get_interface_markers(mesh, submesh)
        if not interface_markers:
            raise ValueError(f"No interface markers found between parent mesh and submesh_{idx}")
        bcs.append(DirichletBC(space, u_sub, interface_markers))

        clayton_outer = sign * (1 / c_sub) * ((u_n_components[idx] - u_nm1_components[idx]) / dt) * v_components[idx]
        for marker in get_shared_exterior_markers(mesh, submesh):
            F += clayton_outer * ds_ext(marker)

    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1, bcs=bcs)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "preonly", "pc_type": "jacobi"}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)
    return solver, u_np1, u_n, u_nm1, tuple(u_n0_subspaces)


def main():
    ensemble_size = 1
    my_ensemble = Ensemble(COMM_WORLD, ensemble_size)

    num_sources = my_ensemble.ensemble_comm.size
    source_number = my_ensemble.ensemble_comm.rank

    dt = 0.002
    final_time = 1.0
    nx, ny = 80, 80

    mesh = UnitSquareMesh(nx, ny, comm=my_ensemble.comm)
    x, z = SpatialCoordinate(mesh)
    DQ0 = FunctionSpace(mesh, "DG", 0)
    submesh_left = mark_submesh(mesh, DQ0, x < 0.1, 999)
    submesh_right = mark_submesh(mesh, DQ0, x > 0.9, 998)
    submesh_bottom = mark_submesh(mesh, DQ0, z > 0.9, 997)
    dx0 = Measure("dx", domain=mesh, intersect_measures=(Measure("dx", submesh_left), Measure("dx", submesh_right)))

    V0 = FunctionSpace(mesh, "KMV", 1)
    V1 = FunctionSpace(submesh_left, "KMV", 1)
    V2 = FunctionSpace(submesh_right, "KMV", 1)
    V3 = FunctionSpace(submesh_bottom, "KMV", 1)
    quad_rule0 = finat.quadrature.make_quadrature(
        V0.finat_element.cell, V0.ufl_element().degree(), "KMV"
    )
    frequency_peak = 7.0
    source_locations = np.linspace((0.3, 0.1), (0.7, 0.1), num_sources)

    V = V0 * V1 * V2 * V3
    c_true = Function(V0).interpolate(
        1.75 + 0.25 * tanh(200 * (0.125 - sqrt((x - 0.5) ** 2 + (z - 0.5) ** 2)))
    )

    source_mesh = VertexOnlyMesh(mesh, [source_locations[source_number]])
    V_s = FunctionSpace(source_mesh, "DG", 0)

    d_s = Function(V_s)
    d_s.interpolate(1.0)

    source_cofunction = assemble(d_s * TestFunction(V_s) * dx)
    q_s = Cofunction(V0.dual()).interpolate(source_cofunction)

    total_steps = int(final_time / dt) + 1

    f = Cofunction(V.dual())
    solver, u_np1, u_n, u_nm1, u_n0_subspaces = wave_equation_solver(
        c_true, f, dt, V, dx0, quad_rule0
    )
    u_n0, _, _, _ = u_n.subfunctions
    u_np10, u_np11, u_np12, u_np13 = u_np1.subfunctions
    transition_width = 0.1
    x_sub_left, _ = SpatialCoordinate(submesh_left)
    x_sub_right, _ = SpatialCoordinate(submesh_right)
    _, z_sub_bottom = SpatialCoordinate(submesh_bottom)
    weight_sub_expr_left = conditional(
        x_sub_left < transition_width,
        (transition_width - x_sub_left) / transition_width,
        0.0,
    )
    weight_sub_expr_right = conditional(
        x_sub_right > (1.0 - transition_width),
        (x_sub_right - (1.0 - transition_width)) / transition_width,
        0.0,
    )
    weight_sub_expr_bottom = conditional(
        z_sub_bottom > (1.0 - transition_width),
        (z_sub_bottom - (1.0 - transition_width)) / transition_width,
        0.0,
    )
    w_subspaces = [
        Function(V1).interpolate(weight_sub_expr_left),
        Function(V2).interpolate(weight_sub_expr_right),
        Function(V3).interpolate(weight_sub_expr_bottom),
    ]
    w_mesh_spaces = [Function(V0) for _ in range(3)]
    habc_sums = [Function(V0) for _ in range(3)]
    submesh_components = [u_np11, u_np12, u_np13]
    VTKFile("weight.pvd").write(w_subspaces[0])
    output_pvd = "acoustic_solution.pvd"
    output_dir = "acoustic_solution"
    output_pvd_sub_left = "acoustic_solution_submesh_left.pvd"
    output_pvd_sub_right = "acoustic_solution_submesh_right.pvd"
    output_pvd_sub_bottom = "acoustic_solution_submesh_bottom.pvd"
    cleanup_outputs(
        output_pvd, output_pvd_sub_left, output_pvd_sub_right,
        output_pvd_sub_bottom, output_dir=output_dir)

    output_file = VTKFile(output_pvd)
    output_file_sub_left = VTKFile(output_pvd_sub_left)
    output_file_sub_right = VTKFile(output_pvd_sub_right)
    output_file_sub_bottom = VTKFile(output_pvd_sub_bottom)
    submesh_output_files = [
        output_file_sub_left,
        output_file_sub_right,
        output_file_sub_bottom,
    ]

    V_plot = FunctionSpace(mesh, "CG", 1)
    u_plot = Function(V_plot, name="acoustic_pressure")
    divergence_config = DivergenceConfig()
    previous_norm = None

    for step in range(total_steps):
        f.sub(0).assign(ricker_wavelet(step * dt, frequency_peak) * q_s)
        for u_n0_sub in u_n0_subspaces:
            u_n0_sub.interpolate(u_n0, allow_missing_dofs=True)

        solver.solve()

        for w_sub, u_np_sub, habc_sum, w_mesh in zip(
            w_subspaces,
            submesh_components,
            habc_sums,
            w_mesh_spaces,
        ):
            habc_sum.interpolate(w_sub * u_np_sub, allow_missing_dofs=True)
            w_mesh.interpolate(w_sub, allow_missing_dofs=True)
            u_np10.interpolate((1.0 - w_mesh) * u_np10 + habc_sum)

        if step % divergence_config.check_every == 0:
            previous_norm = check_divergence(
                u_np10,
                step,
                previous_norm,
                growth_factor=divergence_config.growth_factor,
                abs_limit=divergence_config.abs_limit,
            )

        u_nm1.assign(u_n)
        u_n.assign(u_np1)
        if step % 10 == 0:
            print(f"Step {step}/{total_steps}")
            u_plot.interpolate(u_np10)
            output_file.write(u_plot)

            for output_sub_file, u_n0_sub in zip(submesh_output_files, u_n0_subspaces):
                output_sub_file.write(u_n0_sub)

if __name__ == "__main__":
    main()
