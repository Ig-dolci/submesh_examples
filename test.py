from firedrake import *
import finat


def get_interface_markers(parent_mesh, child_mesh):
    parent_exterior = {int(marker) for marker in parent_mesh.exterior_facets.unique_markers}
    child_exterior = {int(marker) for marker in child_mesh.exterior_facets.unique_markers}
    return tuple(sorted(child_exterior - parent_exterior))


nx, ny = 20, 20
mesh = UnitSquareMesh(nx, ny, quadrilateral=True)
x, y = SpatialCoordinate(mesh)
DG0 = FunctionSpace(mesh, "DG", 0)

indicator_function = Function(DG0).interpolate(conditional(x < 0.2, 1, 0))
mesh.mark_entities(indicator_function, 999)
submesh = Submesh(mesh, 2, 999)

Vsub = FunctionSpace(submesh, "CG", 1)
Vmesh = FunctionSpace(mesh, "CG", 1)

V = Vmesh * Vsub

u, usub = TrialFunction(V)
v, vsub = TestFunction(V)

f = Function(Vmesh)
dx_mesh = Measure("dx", domain=mesh, intersect_measures=(Measure("dx", submesh),))
dx_sub = Measure("dx", domain=submesh, intersect_measures=(Measure("dx", mesh),))
ds_sub_int = Measure("ds", domain=submesh, intersect_measures=(Measure("dS", mesh),))
f.interpolate((1+8*pi*pi)*cos(x*pi*2)*cos(y*pi*2))
F = (inner(grad(u), grad(v)) + inner(u, v)) * dx_mesh
interface_markers = get_interface_markers(mesh, submesh)
if not interface_markers:
    raise ValueError("No interface markers found between parent mesh and submesh")
F -= inner(f, v) * dx_mesh
F += inner(grad(usub), grad(vsub)) * dx_sub
solution = Function(V)
eq_interface = inner(usub - u('+'), vsub) * ds_sub_int(interface_markers) == inner(Constant(0.0), vsub) * ds_sub_int(interface_markers)
interface_bc = EquationBC(eq_interface, solution, interface_markers, V=V.sub(1))

sol_mesh, sol_sub = split(solution)
velocity_mesh = Function(Vmesh)
# interface_markers = get_interface_markers(mesh, submesh)
# dx = Measure("dx", domain=mesh)

# inner(grad(usub), grad(vsub)) * dx + 
problem = LinearVariationalProblem(lhs(F), rhs(F), solution, bcs=[interface_bc])
solver = LinearVariationalSolver(problem,
                                 solver_parameters={'ksp_type': 'preonly', 'pc_type': 'lu'})
solver.solve()

VTKFile("solution.pvd").write(solution.sub(0))
VTKFile("solution_sub.pvd").write(solution.sub(1))
