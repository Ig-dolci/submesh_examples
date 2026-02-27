import os

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
                         quad_rule0, quad_rule1):
    u = TrialFunction(V)
    v = TestFunction(V)
    u0, u1 = split(u)
    v0, v1 = split(v)
    u_n = Function(V)
    u_nm1 = Function(V)
    u_np1 = Function(V)
    u_np10, u_n1 = u_np1.subfunctions
    u_n0, _ = u_n.subfunctions
    u_nm10, u_nm1_1 = u_nm1.subfunctions
    m = 1 / (c * c)
    time_term = m * (u0 - 2.0 * u_n0 + u_nm10) / Constant(dt**2) * v0 * dx0(scheme=quad_rule0)
    a = dot(grad(u_n0), grad(v0)) * dx0(scheme=quad_rule0)
    F = a + time_term
    # time_term + a
    # Clayton's A1 condition
    nf = (1 / c) * ((u1 - u_n1) / dt) * v1 * dx1(scheme=quad_rule1) + dot(u_n1.dx(0), v1) * dx1(scheme=quad_rule1)
    F += nf + inner(u0 - u1, v1) * dx1(scheme=quad_rule1)

    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "preonly", "pc_type": "jacobi"}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)
    return solver, u_np10, u_n0, u_nm10, u1, u_n1


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
    solver, u_np10, u_n0, u_nm10, u1, u_n1 = wave_equation_solver(
        c_true, f, dt, V, dx0, dx1, quad_rule0, quad_rule1
    )
    M = 0.1
    weight = (M - x)/M
    output_file = VTKFile("acoustic_solution.pvd")
    u_till = Function(V0)
    for step in range(total_steps):
        f.sub(0).assign(ricker_wavelet(step * dt, frequency_peak) * q_s)
        solver.solve()
        u_till.interpolate(u_n1, allow_missing_dofs=True)
        # u_np10.interpolate((1 - weight) * u_np10 + weight * u_till)
        u_nm10.assign(u_n0)
        u_n0.assign(u_np10)
        if step % 10 == 0:
            print(f"Step {step}/{total_steps}")
            output_file.write(u_till)


if __name__ == "__main__":
    main()
