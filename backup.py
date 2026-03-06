import finat
import numpy as np
from firedrake import *


def ricker_wavelet(t, fs, amp=1.0):
    ts = 1.5
    t0 = t - ts * np.sqrt(6.0) / (np.pi * fs)
    omega2 = (2.0 * np.pi * fs) * (2.0 * np.pi * fs)
    return amp * (1.0 - 0.5 * omega2 * t0 * t0) * np.exp(-0.25 * omega2 * t0 * t0)


def get_interface_markers(parent_mesh, child_mesh):
    parent_exterior = {int(marker) for marker in parent_mesh.exterior_facets.unique_markers}
    child_exterior = {int(marker) for marker in child_mesh.exterior_facets.unique_markers}
    return tuple(sorted(child_exterior - parent_exterior))


def get_submesh_interface_markers(parent_mesh, mesh_a, mesh_b):
    parent_exterior = {int(marker) for marker in parent_mesh.exterior_facets.unique_markers}
    a_exterior = {int(marker) for marker in mesh_a.exterior_facets.unique_markers}
    b_exterior = {int(marker) for marker in mesh_b.exterior_facets.unique_markers}
    return tuple(sorted((a_exterior & b_exterior) - parent_exterior))



def mark_submesh(mesh, dq0, indicator_expr, marker):
    indicator = Function(dq0).interpolate(conditional(indicator_expr, 1, 0))
    mesh.mark_entities(indicator, marker)
    return Submesh(mesh, 2, marker)


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
    dt_const = Constant(dt)
    dt2_const = Constant(dt**2)
    dx0_rule = dx0(scheme=quad_rule0) if quad_rule0 is not None else dx0
    F = m * (u0 - 2.0 * u_n0 + u_nm10) / dt2_const * v0 * dx0_rule + dot(grad(u0), grad(v0)) * dx0_rule

    bcs = []
    direction_signs = (-1.0, 1.0, 1.0)
    direction_axes = (0, 0, 1)
    for idx, (space, submesh, c_sub) in enumerate(
        zip(subspaces, submeshes, c_subspaces),
        start=1,
    ):
        u_i = u_components[idx]
        v_i = v_components[idx]
        u_n_i = u_n_components[idx]
        sign = direction_signs[idx - 1]
        axis = direction_axes[idx - 1]

        dx_i = Measure("dx", domain=submesh, intersect_measures=(Measure("dx", mesh),))
        ds_i_int = Measure("ds", domain=submesh, intersect_measures=(Measure("dS", mesh),))

        one_way_sub = (
            (1 / c_sub) * (u_i - u_n_i) / dt_const * v_i * dx_i
            + sign * u_i.dx(axis) * v_i * dx_i
        )
        F += one_way_sub

        interface_markers = get_interface_markers(mesh, submesh)
        if not interface_markers:
            raise ValueError(f"No interface markers found between parent mesh and submesh_{idx}")

        eq_interface = inner(u_i - u0('+'), v_i) * ds_i_int(interface_markers) == inner(Constant(0.0), v_i) * ds_i_int(interface_markers)
        bcs.append(EquationBC(eq_interface, u_np1, interface_markers, V=space))


    lin_var = LinearVariationalProblem(lhs(F), rhs(F) + source_function, u_np1, bcs=bcs)
    solver_parameters = {"mat_type": "matfree", "ksp_type": "gmres", "pc_type": "bjacobi", "ksp_rtol": 1.0e-8}
    solver = LinearVariationalSolver(lin_var, solver_parameters=solver_parameters)

    return solver, u_np1, u_n, u_nm1, tuple(u_n0_subspaces)


def main():
    ensemble_size = 1
    my_ensemble = Ensemble(COMM_WORLD, ensemble_size)
    source_number = my_ensemble.ensemble_comm.rank

    dt = 0.001
    final_time = 1.0
    nx, ny = 80, 80
    boundary_distance = Constant(0.2)
    domain_length = 1.5
    mesh = SquareMesh(nx, ny, domain_length, comm=my_ensemble.comm)
    x, z = SpatialCoordinate(mesh)
    distance_left = x
    distance_right = domain_length - x
    distance_top = domain_length - z
    DQ0 = FunctionSpace(mesh, "DG", 0)
    submesh_left = mark_submesh(mesh, DQ0, distance_left < boundary_distance, 999)
    submesh_right = mark_submesh(mesh, DQ0, distance_right < boundary_distance, 998)
    submesh_bottom = mark_submesh(
        mesh,
        DQ0,
        And(
            distance_top < boundary_distance,
            And(distance_left > boundary_distance, distance_right > boundary_distance),
        ),
        997,
    )
    dx0 = Measure(
        "dx",
        domain=mesh,
        intersect_measures=(
            Measure("dx", submesh_left),
            Measure("dx", submesh_right),
            Measure("dx", submesh_bottom),
        ),
    )

    V0 = FunctionSpace(mesh, "KMV", 1)
    V1 = FunctionSpace(submesh_left, "KMV", 1)
    V2 = FunctionSpace(submesh_right, "KMV", 1)
    V3 = FunctionSpace(submesh_bottom, "KMV", 1)
    quad_rule0 = finat.quadrature.make_quadrature(
        V0.finat_element.cell, V0.ufl_element().degree(), "KMV"
    )
    frequency_peak = 7.0
    source_locations = np.array([(0.75, 0.75)])
    V = V0 * V1 * V2 * V3
    c_true = Function(V0).interpolate(2.0)

    source_mesh = VertexOnlyMesh(mesh, [source_locations[source_number]])
    V_s = FunctionSpace(source_mesh, "DG", 0)

    d_s = Function(V_s)
    d_s.interpolate(1.0)

    source_cofunction = assemble(d_s * TestFunction(V_s) * dx)
    q_s = Cofunction(V0.dual()).interpolate(source_cofunction)

    total_steps = int(final_time / dt) + 1

    f = Cofunction(V.dual())
    f_no_submesh = Cofunction(V0.dual())
    solver, u_np1, u_n, u_nm1, u_n0_subspaces = wave_equation_solver(
        c_true, f, dt, V, dx0, quad_rule0
    )

    u_n0, _, _, _ = u_n.subfunctions
    u_np10, u_np11, u_np12, u_np13 = u_np1.subfunctions
    transition_width = boundary_distance
    x_sub_left, _ = SpatialCoordinate(submesh_left)
    x_sub_right, _ = SpatialCoordinate(submesh_right)
    _, z_sub_bottom = SpatialCoordinate(submesh_bottom)
    distance_left_sub = x_sub_left
    distance_right_sub = domain_length - x_sub_right
    distance_top_sub = domain_length - z_sub_bottom
    weight_sub_expr_left = conditional(
        distance_left_sub < transition_width,
        (transition_width - distance_left_sub) / transition_width,
        0.0,
    )
    weight_sub_expr_right = conditional(
        distance_right_sub < transition_width,
        (transition_width - distance_right_sub) / transition_width,
        0.0,
    )
    weight_sub_expr_bottom = conditional(
        distance_top_sub < transition_width,
        (transition_width - distance_top_sub) / transition_width,
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

    receiver_mesh = VertexOnlyMesh(mesh, np.array([(0.75, 0.75)]))
    V_r = FunctionSpace(receiver_mesh, "DG", 0)
    receiver_submesh = Function(V_r)
    rec_array_submesh = []
    for step in range(total_steps):
        source_value = ricker_wavelet(step * dt, frequency_peak)
        f.sub(0).assign(source_value * q_s)
        f_no_submesh.assign(source_value * q_s)

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

        receiver_submesh.interpolate(u_np10)
        rec_array_submesh.append(float(receiver_submesh.dat.data_ro[0]))
        
        u_nm1.assign(u_n)
        u_n.assign(u_np1)

        if step % 100 == 0:
            print(f"Step {step}/{total_steps}, time={step*dt:.3f})")

    VTKFile("solution.pvd").write(u_np1.sub(0))


if __name__ == "__main__":
    main()
