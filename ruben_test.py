from firedrake import *
import finat


def make_layered_velocity(V0, z):
    velocity = Function(V0)
    velocity.interpolate(
        conditional(
            z < 1.0 / 6.0,
            1.5,
            conditional(
                z < 2.0 / 6.0,
                1.7,
                conditional(
                    z < 3.0 / 6.0,
                    1.9,
                    conditional(
                        z < 4.0 / 6.0,
                        2.1,
                        conditional(
                            z < 5.0 / 6.0,
                            2.3,
                            2.5,
                        ),
                    ),
                ),
            ),
        )
    )
    return velocity


def get_interface_markers(parent_mesh, child_mesh):
    parent_exterior = {int(marker) for marker in parent_mesh.exterior_facets.unique_markers}
    child_exterior = {int(marker) for marker in child_mesh.exterior_facets.unique_markers}
    return tuple(sorted(child_exterior - parent_exterior))


def solve_submesh_projection(mesh, submesh, velocity, derivative_axis):
    V = FunctionSpace(submesh, "KMV", 1)
    solution = Function(V)
    velocity_sub = Function(V)
    velocity_sub.interpolate(velocity, allow_missing_dofs=True)

    interface_markers = get_interface_markers(velocity.ufl_domain(), submesh)
    if not interface_markers:
        raise ValueError("No interface markers found between parent mesh and submesh")
    dx = Measure("dx", domain=mesh)
    dx_sub = Measure("dx", domain=submesh, intersect_measures=(Measure("dx", velocity.ufl_domain()),))
    u = TrialFunction(V)
    v = TestFunction(V)

    a = u.dx(derivative_axis) * v * dx_sub
    L = Constant(0.0) * v * dx_sub
    bc_interface = DirichletBC(V, velocity_sub, interface_markers)

    problem = LinearVariationalProblem(a, L, solution, bcs=[bc_interface])
    solver = LinearVariationalSolver(problem)
    solver.solve()
    return solution


def main():
    nx, ny = 20, 20
    mesh = UnitSquareMesh(nx, ny)
    x, z = SpatialCoordinate(mesh)
    DQ0 = FunctionSpace(mesh, "DG", 0)

    indicator_function = Function(DQ0).interpolate(conditional(Or(x < 0.2, x > 0.8), 1, 0))
    indicator_function1 = Function(DQ0).interpolate(conditional(z > 0.8, 1, 0))
    mesh.mark_entities(indicator_function, 999)
    mesh.mark_entities(indicator_function1, 998)

    submesh = Submesh(mesh, 2, 999)
    submesh1 = Submesh(mesh, 2, 998)

    V0 = FunctionSpace(mesh, "KMV", 1)
    finat.quadrature.make_quadrature(V0.finat_element.cell, V0.ufl_element().degree(), "KMV")
    velocity = make_layered_velocity(V0, z)
    VTKFile("velocity.pvd").write(velocity)

    velocity1 = solve_submesh_projection(submesh, velocity, derivative_axis=0)
    velocity2 = solve_submesh_projection(submesh1, velocity, derivative_axis=1)

    VTKFile("velocity_submesh.pvd").write(velocity1)
    VTKFile("velocity_submesh1.pvd").write(velocity2)


if __name__ == "__main__":
    main()

