import os
import shutil

import finat
import numpy as np
from firedrake import *
from firedrake.adjoint import *


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
    u0, u1 = split(u)
    v0, v1 = split(v)
    u_n = Function(V)
    u_nm1 = Function(V)
    u_np1 = Function(V)
    u_n0, u_n1 = u_n.subfunctions
    u_nm10, u_nm1_1 = u_nm1.subfunctions
    V1 = V.sub(1)
    mesh = V.sub(0).mesh()
    submesh = V1.mesh()
    c_sub = Function(V1).interpolate(c, allow_missing_dofs=True)
    u_n0_sub = Function(V1).interpolate(u_n0, allow_missing_dofs=True)
    m = 1 / (c * c)
    time_term = m * (u0 - 2.0 * u_n0 + u_nm10) / Constant(dt**2) * v0 * dx0(scheme=quad_rule0)
    a = dot(grad(u_n0), grad(v0)) * dx0(scheme=quad_rule0)
    F = a + time_term
    ds1_ext = Measure("ds", domain=submesh, intersect_measures=(Measure("ds", mesh),))
    u_sub = Function(V1).interpolate(u_n0, allow_missing_dofs=True)
    interface_markers = get_interface_markers(mesh, submesh)
    if not interface_markers:
        raise ValueError("No interface markers found between parent mesh and submesh")
    interface_dirichlet = DirichletBC(V1, u_sub, interface_markers)
    clayton_outer = (1 / c_sub) * ((u_n1 - u_nm1_1) / dt) * v1
    exterior_markers = get_shared_exterior_markers(mesh, submesh)
    for marker in exterior_markers:
        F += clayton_outer * ds1_ext(marker)

    bcs = [interface_dirichlet]

    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1, bcs=bcs)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "preonly", "pc_type": "jacobi"}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)
    return solver, u_np1, u_n, u_nm1, u_n0_sub


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
    indicator_function = Function(DQ0).interpolate(conditional(x < 0.1, 1, 0))
    mesh.mark_entities(indicator_function, 999)
    submesh = Submesh(mesh, 2, 999)
    dx0 = Measure("dx", domain=mesh, intersect_measures=(Measure("dx", submesh),))
    dx1 = Measure("dx", domain=submesh, intersect_measures=(Measure("dx", mesh),))

    V0 = FunctionSpace(mesh, "KMV", 1)
    V1 = FunctionSpace(submesh, "KMV", 1)
    quad_rule0 = finat.quadrature.make_quadrature(
        V0.finat_element.cell, V0.ufl_element().degree(), "KMV"
    )
    frequency_peak = 7.0
    source_locations = np.linspace((0.3, 0.1), (0.7, 0.1), num_sources)

    V = V0 * V1
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
    solver, u_np1, u_n, u_nm1, u_n0_sub = wave_equation_solver(
        c_true, f, dt, V, dx0, quad_rule0
    )
    u_n0, u_n1 = u_n.subfunctions
    u_np10, u_np11 = u_np1.subfunctions
    transition_width = 0.1
    x_sub, _ = SpatialCoordinate(submesh)
    weight_sub_expr = conditional(
        x_sub < transition_width,
        (transition_width - x_sub) / transition_width,
        0.0,
    )
    w_sub = Function(V1).interpolate(weight_sub_expr)
    w_mesh = Function(V0)
    habc_sum = Function(V0)
    VTKFile("weight.pvd").write(w_sub)
    output_pvd = "acoustic_solution.pvd"
    output_dir = "acoustic_solution"
    output_pvd_sub = "acoustic_solution_submesh.pvd"
    cleanup_outputs(output_pvd, output_pvd_sub, output_dir=output_dir)

    output_file = VTKFile(output_pvd)
    output_file_sub = VTKFile(output_pvd_sub)
    V_plot = FunctionSpace(mesh, "CG", 1)
    u_plot = Function(V_plot, name="acoustic_pressure")
    divergence_check_every = 5
    divergence_growth_factor = 50.0
    divergence_abs_limit = 1.0e6
    previous_norm = None

    for step in range(total_steps):
        f.sub(0).assign(ricker_wavelet(step * dt, frequency_peak) * q_s)
        u_n0_sub.interpolate(u_n0, allow_missing_dofs=True)
        solver.solve()
        habc_sum.interpolate(w_sub * u_np11, allow_missing_dofs=True)
        w_mesh.interpolate(w_sub, allow_missing_dofs=True)
        u_np10.interpolate((1.0 - w_mesh) * u_np10 + habc_sum)

        if step % divergence_check_every == 0:
            previous_norm = check_divergence(
                u_np10,
                step,
                previous_norm,
                growth_factor=divergence_growth_factor,
                abs_limit=divergence_abs_limit,
            )

        u_nm1.assign(u_n)
        u_n.assign(u_np1)
        if step % 10 == 0:
            print(f"Step {step}/{total_steps}")
            u_plot.interpolate(u_np10)
            output_file.write(u_plot)
            output_file_sub.write(u_n0_sub)


if __name__ == "__main__":
    main()
