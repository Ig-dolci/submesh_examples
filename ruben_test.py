from firedrake import *
import finat
import numpy as np


nx, ny = 20, 20
mesh = UnitSquareMesh(nx, ny)
x, z = SpatialCoordinate(mesh)
DQ0 = FunctionSpace(mesh, "DG", 0)
indicator_function = Function(DQ0).interpolate(conditional(x < 0.2, 1, 0))
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

velocity = Function(V0)
velocity.interpolate(
    conditional(
        z < 1.0/6.0,
        1.5,
        conditional(
            z < 2.0/6.0,
            1.7,
            conditional(
                z < 3.0/6.0,
                1.9,
                conditional(
                    z < 4.0/6.0,
                    2.1,
                    conditional(
                        z < 5.0/6.0,
                        2.3,
                        2.5,
                    ),
                ),
            ),
        ),
    )
)

VTKFile("velocity.pvd").write(velocity)

velocity1 = Function(V1)
ds1 = Measure("ds", domain=submesh, intersect_measures=(Measure("dS", mesh),))

# Get the velocity values an the coordinates of the mesh that
# are on the interface between the mesh and the submesh
mesh_ext = set(int(m) for m in mesh.exterior_facets.unique_markers)
subm_ext = set(int(m) for m in submesh.exterior_facets.unique_markers)
interface_markers = tuple(sorted(subm_ext - mesh_ext))
if not interface_markers:
    raise ValueError("No interface markers found between parent mesh and submesh")

# Map parent-mesh velocity to submesh space
velocity_sub = Function(V1)
velocity_sub.interpolate(velocity, allow_missing_dofs=True)

u = TrialFunction(V1)
v = TestFunction(V1)

# Poisson problem on submesh with Dirichlet condition on interface (ds1 markers)
a = u.dx(0) * v * dx1
L = Constant(0.0) * v * dx1
bc_interface = DirichletBC(V1, velocity_sub, interface_markers)

problem = LinearVariationalProblem(a, L, velocity1, bcs=[bc_interface])
solver = LinearVariationalSolver(problem)
solver.solve()

VTKFile("velocity_submesh.pvd").write(velocity1)

