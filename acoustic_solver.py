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


def wave_equation_solver(c, source_function, dt, V):
    u = TrialFunction(V)
    v = TestFunction(V)
    u_np1 = Function(V)
    u_n = Function(V)
    u_nm1 = Function(V)

    quad_rule = finat.quadrature.make_quadrature(
        V.finat_element.cell, V.ufl_element().degree(), "KMV"
    )

    m = 1 / (c * c)
    time_term = m * (u - 2.0 * u_n + u_nm1) / Constant(dt**2) * v * dx(scheme=quad_rule)
    a = dot(grad(u_n), grad(v)) * dx(scheme=quad_rule)
    F = time_term + a

    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "preonly", "pc_type": "jacobi"}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)
    return solver, u_np1, u_n, u_nm1


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

    frequency_peak = 7.0
    source_locations = np.linspace((0.3, 0.1), (0.7, 0.1), num_sources)
    receiver_locations = np.linspace((0.2, 0.9), (0.8, 0.9), 20)

    V = FunctionSpace(mesh, "KMV", 1)
    x, z = SpatialCoordinate(mesh)
    c_true = Function(V).interpolate(
        1.75 + 0.25 * tanh(200 * (0.125 - sqrt((x - 0.5) ** 2 + (z - 0.5) ** 2)))
    )

    source_mesh = VertexOnlyMesh(mesh, [source_locations[source_number]])
    V_s = FunctionSpace(source_mesh, "DG", 0)

    d_s = Function(V_s)
    d_s.interpolate(1.0)

    source_cofunction = assemble(d_s * TestFunction(V_s) * dx)
    q_s = Cofunction(V.dual()).interpolate(source_cofunction)

    total_steps = int(final_time / dt) + 1

    f = Cofunction(V.dual())
    solver, u_np1, u_n, u_nm1 = wave_equation_solver(c_true, f, dt, V)
    output_file = VTKFile("acoustic_solution.pvd")
    for step in range(total_steps):
        f.assign(ricker_wavelet(step * dt, frequency_peak) * q_s)
        solver.solve()
        u_nm1.assign(u_n)
        u_n.assign(u_np1)
        if step % 10 == 0:
            print(f"Step {step}/{total_steps}")
            output_file.write(u_n)


if __name__ == "__main__":
    main()
