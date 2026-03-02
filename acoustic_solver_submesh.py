import os
import shutil

import finat
import numpy as np
from firedrake import *
from firedrake.adjoint import *
from pyadjoint.reduced_functional_numpy import ReducedFunctionalNumPy
from scipy.optimize import minimize as scipy_minimize


def ricker_wavelet(t, fs, amp=1.0):
    ts = 1.5
    t0 = t - ts * np.sqrt(6.0) / (np.pi * fs)
    omega2 = (2.0 * np.pi * fs) * (2.0 * np.pi * fs)
    return amp * (1.0 - 0.5 * omega2 * t0 * t0) * np.exp(-0.25 * omega2 * t0 * t0)


def wave_equation_solver(c, source_function, dt, V, dx0, dx1,
                         quad_rule0, quad_rule1, x):
    u = TrialFunction(V)
    v = TestFunction(V)
    u0, u1 = split(u)
    v0, v1 = split(v)
    u_n = Function(V)
    u_nm1 = Function(V)
    u_np1 = Function(V)
    u_np10, _ = u_np1.subfunctions
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
    M = 0.1
    clayton_bc = (1 / c_sub) * ((u_n1 - u_nm1_1) / dt) * v1 * dx1(scheme=quad_rule1) - dot(u1.dx(0), v1) * dx1(scheme=quad_rule1)
    ds1_int = Measure("ds", domain=submesh, intersect_measures=(Measure("dS", mesh),))
    penalty = Constant(1.0 / dt)
    interface_dirichlet = penalty * (u1 - u_n0_sub) * v1 * ds1_int
    F += clayton_bc + interface_dirichlet
    # + inner(u_n0 - (1-weight)*u_n0 - weight * u_n1, v1) * dx1(scheme=quad_rule1)
    # F += inner(u_n0  - u_n1, v1) * dx1(scheme=quad_rule1)
    mesh_exterior_markers = set(int(marker) for marker in mesh.exterior_facets.unique_markers)
    submesh_exterior_markers = tuple(int(marker) for marker in submesh.exterior_facets.unique_markers)
    exterior_markers = tuple(marker for marker in submesh_exterior_markers if marker in mesh_exterior_markers)
    bcs = []
    if exterior_markers:
        bc_submesh_ext = DirichletBC(V.sub(1), Constant(0.0), exterior_markers)
        bcs.append(bc_submesh_ext)

    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1, bcs=bcs)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "preonly", "pc_type": "jacobi"}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)
    return solver, u_np1, u_n, u_nm1, u_n0_sub


def main():
    M = 1
    my_ensemble = Ensemble(COMM_WORLD, M)

    num_sources = my_ensemble.ensemble_comm.size
    source_number = my_ensemble.ensemble_comm.rank

    dt = 0.002
    final_time = 1.0
    nx, ny = 80, 80
    ftol = 1e-2

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
    quad_rule1 = finat.quadrature.make_quadrature(
        V1.finat_element.cell, V1.ufl_element().degree(), "KMV"
    )
    frequency_peak = 7.0
    source_locations = np.linspace((0.3, 0.1), (0.7, 0.1), num_sources)

    V = V0*V1
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
        c_true, f, dt, V, dx0, dx1, quad_rule0, quad_rule1, x
    )
    u_n0, u_n1 = u_n.subfunctions
    u_np10, u_np11 = u_np1.subfunctions
    M = 0.1
    x_sub, _ = SpatialCoordinate(submesh)
    weight_sub_expr = conditional(x_sub < M, (M - x_sub) / M, 0.0)
    w_sub = Function(V1).interpolate(weight_sub_expr)
    w_mesh = Function(V0)
    habc_sum = Function(V0)
    VTKFile("weight.pvd").write(w_sub)
    output_pvd = "acoustic_solution.pvd"
    output_dir = "acoustic_solution"
    if os.path.exists(output_pvd):
        os.remove(output_pvd)
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)

    output_file = VTKFile(output_pvd)
    V_plot = FunctionSpace(mesh, "CG", 1)
    u_plot = Function(V_plot, name="acoustic_pressure")
    for step in range(total_steps):
        f.sub(0).assign(ricker_wavelet(step * dt, frequency_peak) * q_s)
        u_n0_sub.interpolate(u_n0, allow_missing_dofs=True)
        solver.solve()
        habc_sum.interpolate(w_sub * u_np11, allow_missing_dofs=True)
        w_mesh.interpolate(w_sub, allow_missing_dofs=True)
        u_np10.interpolate((1.0 - w_mesh) * u_np10 + habc_sum)
        u_nm1.assign(u_n)
        u_n.assign(u_np1)
        if step % 10 == 0:
            print(f"Step {step}/{total_steps}")
            u_plot.interpolate(u_np10)
            output_file.write(u_plot)


if __name__ == "__main__":
    main()
