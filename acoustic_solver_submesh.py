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
    u_splits = split(u)
    v_splits = split(v)
    u0 = u_splits[0]
    v0 = v_splits[0]
    u_n = Function(V)
    u_nm1 = Function(V)
    u_np1 = Function(V)
    subs = u_n.subfunctions
    subs_m1 = u_nm1.subfunctions
    u_n0 = subs[0]
    u_nm10 = subs_m1[0]
    mesh = V.sub(0).mesh()

    m = 1 / (c * c)
    time_term = m * (u0 - 2.0 * u_n0 + u_nm10) / Constant(dt**2) * v0 * dx0(scheme=quad_rule0)
    a = dot(grad(u_n0), grad(v0)) * dx0(scheme=quad_rule0)
    F = a + time_term

    bcs = []
    u_n0_subs = []
    num_submeshes = len(V) - 1
    for i in range(num_submeshes):
        idx = i + 1
        V_sub = V.sub(idx)
        submesh_i = V_sub.mesh()
        c_sub = Function(V_sub).interpolate(c, allow_missing_dofs=True)
        u_sub = Function(V_sub).interpolate(u_n0, allow_missing_dofs=True)
        u_n0_subs.append(u_sub)

        interface_markers = get_interface_markers(mesh, submesh_i)
        if not interface_markers:
            raise ValueError(f"No interface markers for submesh {i}")
        bcs.append(DirichletBC(V_sub, u_sub, interface_markers))

        ds_ext = Measure("ds", domain=submesh_i, intersect_measures=(Measure("ds", mesh),))
        exterior_markers = get_shared_exterior_markers(mesh, submesh_i)
        u_ni = u_splits[idx]
        v_ni = v_splits[idx]
        u_nm1i = subs_m1[idx]
        clayton = (1 / c_sub) * ((u_ni - u_nm1i) / dt) * v_ni
        for marker in exterior_markers:
            F += clayton * ds_ext(marker)

    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1, bcs=bcs)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "preonly", "pc_type": "jacobi"}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)
    return solver, u_np1, u_n, u_nm1, u_n0_subs


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
    indicator_right = Function(DQ0).interpolate(conditional(x > 0.9, 1, 0))
    indicator_bottom = Function(DQ0).interpolate(conditional(z < 0.1, 1, 0))
    mesh.mark_entities(indicator_right, 999)
    mesh.mark_entities(indicator_bottom, 998)
    submesh_right = Submesh(mesh, 2, 999)
    submesh_bottom = Submesh(mesh, 2, 998)
    dx0 = Measure("dx", domain=mesh, intersect_measures=(Measure("dx", submesh_right), Measure("dx", submesh_bottom)))

    V0 = FunctionSpace(mesh, "KMV", 1)
    V1_right = FunctionSpace(submesh_right, "KMV", 1)
    V1_bottom = FunctionSpace(submesh_bottom, "KMV", 1)
    quad_rule0 = finat.quadrature.make_quadrature(
        V0.finat_element.cell, V0.ufl_element().degree(), "KMV"
    )
    frequency_peak = 7.0
    source_locations = np.linspace((0.3, 0.1), (0.7, 0.1), num_sources)

    V = V0 * V1_right * V1_bottom
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
    solver, u_np1, u_n, u_nm1, u_n0_subs = wave_equation_solver(
        c_true, f, dt, V, dx0, quad_rule0
    )
    u_n0 = u_n.subfunctions[0]
    u_np10 = u_np1.subfunctions[0]
    u_np1_right = u_np1.subfunctions[1]
    u_np1_bottom = u_np1.subfunctions[2]

    transition_width = 0.1
    # Right boundary weight: ramps 0→1 from x=0.9 to x=1.0
    x_r, _ = SpatialCoordinate(submesh_right)
    weight_right_expr = conditional(
        x_r > 1.0 - transition_width,
        (x_r - (1.0 - transition_width)) / transition_width,
        0.0,
    )
    w_right = Function(V1_right).interpolate(weight_right_expr)
    # Bottom boundary weight: ramps 0→1 from z=0.1 to z=0.0
    _, z_b = SpatialCoordinate(submesh_bottom)
    weight_bottom_expr = conditional(
        z_b < transition_width,
        (transition_width - z_b) / transition_width,
        0.0,
    )
    w_bottom = Function(V1_bottom).interpolate(weight_bottom_expr)

    w_mesh = Function(V0)
    habc_sum = Function(V0)
    w_bottom_parent = Function(V0)
    w_bottom_parent.interpolate(w_bottom, allow_missing_dofs=True)
    habc_bottom = Function(V0)
    w_total = Function(V0)
    VTKFile("weight_right.pvd").write(w_right)
    VTKFile("weight_bottom.pvd").write(w_bottom)
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
        for u_sub in u_n0_subs:
            u_sub.interpolate(u_n0, allow_missing_dofs=True)
        solver.solve()

        # Blend right submesh
        habc_sum.assign(0.0)
        habc_sum.interpolate(w_right * u_np1_right, allow_missing_dofs=True)
        w_mesh.assign(0.0)
        w_mesh.interpolate(w_right, allow_missing_dofs=True)
        # Blend bottom submesh (additive, then clamp)
        habc_bottom.assign(0.0)
        habc_bottom.interpolate(w_bottom * u_np1_bottom, allow_missing_dofs=True)
        habc_sum.interpolate(habc_sum + habc_bottom)
        w_total.interpolate(w_mesh + w_bottom_parent)
        w_mesh.interpolate(conditional(w_total > 1.0, Constant(1.0), w_total))
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
            output_file_sub.write(u_n0_subs[0])


if __name__ == "__main__":
    main()
