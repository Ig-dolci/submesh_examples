# Auto-generated from habc_solver_explained.ipynb

# %% [markdown]
# # Hybrid Absorbing Boundary Condition using Submeshes
#
# This notebook implements a **Hybrid Absorbing Boundary Condition (HABC)** solver for the 2D acoustic wave equation in Firedrake. The idea is to reduce artificial reflections by coupling the physical-domain solution with one-way equations posed on absorbing extended pad domains.
#
# The implementation follows the one-way HABC strategy described in Section 2.2 of Liu & Sen (2018): https://doi.org/10.1088/1742-2140/aadd31.

# %% [markdown]
# ## Acoustic Wave Equation and HABC (one-way extended pad domain formulation)
#
# We solve the second-order acoustic wave equation in the physical domain $\Omega$, and one-way first-order equations in absorbing extended pad domains $\Omega_i$ with $i\in\{L,R,B\}$ (left, right, bottom).
#
# In $\Omega$:
#
# $$
# \frac{1}{c^2}\,\partial_{tt}u_0 - \nabla^2 u_0 = f.
# $$
#
# In each extended pad domain $\Omega_i$:
#
# $$
# \frac{1}{c_i}\,\partial_t u_i + s_i\,\partial_{\alpha_i}u_i = 0, \qquad i\in\{L,R,B\},
# $$
#
# with $(s_i,\alpha_i)=(-1,x)$ on the left domain, $(+1,x)$ on the right domain, and $(+1,z)$ on the bottom domain.
#
# ### Weak form
#
# Let $V = V_0 \times V_L \times V_R \times V_B$ be the mixed space. The semi-discrete coupled weak form at time step $n+1$ is
#
# $$
# \int_{\Omega} \left[
# \frac{1}{c^2}\frac{u_0^{n+1}-2u_0^n+u_0^{n-1}}{\Delta t^2}v_0 + \nabla u_0^{n+1}\cdot\nabla v_0
# \right]dx
#  + \sum_{i\in\{L,R,B\}}\int_{\Omega_i}\left[
# \frac{1}{c_i}\frac{u_i^{n+1}-u_i^n}{\Delta t}v_i + s_i\,\partial_{\alpha_i}u_i^{n+1}v_i
# \right]dx
#  = \langle f^{n+1}, v_0\rangle.
# $$
#
# The coupling between parent and pad-domain fields is imposed on each interface $\Gamma_i$ by
#
# $$
# \int_{\Gamma_i}(u_i^{n+1} - u_0^{n+1,+})v_i\,ds = 0,
# $$
#
# which we enforce with Firedrake `EquationBC`.

# %% [markdown]
# We start by importing the required libraries and defining simulation parameters (time stepping, mesh size, source setup, and extended pad domain markers).

# %%
from typing import Any

import firedrake as fd
import finat
import matplotlib.pyplot as plt
import numpy as np


class SimulationConfig:
    """Configuration for the HABC simulation."""

    dt: float = 0.001
    final_time: float = 1.0
    nx: int = 80
    ny: int = 80
    domain_length: float = 1.5
    boundary_distance: float = 0.2
    frequency_peak: float = 7.0
    source_locations: tuple[tuple[float, float], ...] = ((0.75, 0.75),)
    progress_interval: int = 100
    left_marker: int = 999
    right_marker: int = 998
    bottom_marker: int = 997

    @property
    def total_steps(self) -> int:
        """Return the number of explicit time steps."""
        return int(self.final_time / self.dt) + 1

# %% [markdown]
# Following the Firedrake FWI tutorial pattern, we decompose the source as
#
# $$
# f_s(\mathbf{x}, t) = r(t)\,q_s(\mathbf{x}), \qquad q_s\in V^*.
# $$
#
# Here:
# - `ricker_wavelet(...)` defines the temporal signature $r(t)$;
# - `build_source_term(...)` builds the spatial source cofunction $q_s$ using `VertexOnlyMesh`, `FunctionSpace`, and `Cofunction(...).interpolate(...)`.
#
# This is the same source-injection strategy used in the full-waveform inversion demo, adapted here for the HABC mixed formulation.

# %%
def ricker_wavelet(
    time: float,
    peak_frequency: float,
    amplitude: float = 1.0,
) -> float:
    """Evaluate a Ricker wavelet at a given time."""
    ts = 1.5
    shifted_time = time - ts * np.sqrt(6.0) / (np.pi * peak_frequency)
    omega = 2.0 * np.pi * peak_frequency
    omega_squared = omega * omega
    factor = 1.0 - 0.5 * omega_squared * shifted_time * shifted_time
    return amplitude * factor * np.exp(
        -0.25 * omega_squared * shifted_time * shifted_time
    )


def build_source_term(
    mesh: Any,
    parent_space: fd.FunctionSpace,
    source_location: tuple[float, float],
) -> fd.Cofunction:
    """Project a point source to the dual of the parent function space."""
    source_mesh = fd.VertexOnlyMesh(mesh, [source_location])
    source_space = fd.FunctionSpace(source_mesh, "DG", 0)
    source_density = fd.Function(source_space).interpolate(1.0)
    source_cofunction = fd.assemble(
        source_density * fd.TestFunction(source_space) * fd.dx
    )
    return fd.Cofunction(parent_space.dual()).interpolate(source_cofunction)

# %% [markdown]
# Next, we compute interface markers between the parent mesh and each absorbing extended pad domain. These markers identify where to enforce parent/pad-domain coupling with Firedrake `EquationBC`.

# %%
def get_interface_markers(
    parent_mesh: Any,
    child_mesh: Any,
) -> tuple[int, ...]:
    """Return markers present on a child submesh only.

    Markers shared with the parent mesh exterior are excluded.
    """
    parent_exterior = {
        int(marker)
        for marker in parent_mesh.exterior_facets.unique_markers
    }
    child_exterior = {
        int(marker)
        for marker in child_mesh.exterior_facets.unique_markers
    }
    return tuple(sorted(child_exterior - parent_exterior))


# %% [markdown]
# We now create absorbing extended pad domains as children of the parent mesh. The helper `submeshes(...)` returns the left, right, and bottom domains plus an intersected parent measure used in the coupled variational form.

# %%
def create_submesh(
    mesh: Any,
    dq0: fd.FunctionSpace,
    indicator_expr: Any,
    marker: int,
) -> Any:
    """Mark cells from an indicator expression and create a submesh."""
    indicator = fd.Function(dq0).interpolate(
        fd.conditional(indicator_expr, 1, 0)
    )
    mesh.mark_entities(indicator, marker)
    return fd.Submesh(mesh, 2, marker)


def submeshes(
    mesh: Any,
    boundary_distance: fd.Constant,
    domain_length: float,
    markers: tuple[int, int, int],
) -> tuple[Any, Any, Any, fd.Measure]:
    """Create left/right/top boundary submeshes and intersected measure."""
    left_marker, right_marker, bottom_marker = markers
    x, z = fd.SpatialCoordinate(mesh)
    distance_left = x
    distance_right = domain_length - x
    distance_top = domain_length - z

    dq0 = fd.FunctionSpace(mesh, "DG", 0)
    submesh_left = create_submesh(
        mesh,
        dq0,
        distance_left < boundary_distance,
        left_marker,
    )
    submesh_right = create_submesh(
        mesh,
        dq0,
        distance_right < boundary_distance,
        right_marker,
    )
    submesh_bottom = create_submesh(
        mesh,
        dq0,
        fd.And(
            distance_top < boundary_distance,
            fd.And(
                distance_left > boundary_distance,
                distance_right > boundary_distance,
            ),
        ),
        bottom_marker,
    )

    dx0 = fd.Measure(
        "dx",
        domain=mesh,
        intersect_measures=(
            fd.Measure("dx", submesh_left),
            fd.Measure("dx", submesh_right),
            fd.Measure("dx", submesh_bottom),
        ),
    )
    return submesh_left, submesh_right, submesh_bottom, dx0

# %% [markdown]
# To merge pad-domain solutions back into the parent field, we define linear transition weights in each absorbing extended pad domain. A practical expression is
#
# $$
# w_i = \max\left(0, \frac{\delta - d_i}{\delta}\right), \qquad i\in\{L,R,B\},
# $$
#
# where $d_i$ is the local distance to the parent/pad-domain interface and $\delta$ is the absorbing-pad width (`transition_width`).

# %%
def build_transition_weights(
    submesh_left: Any,
    submesh_right: Any,
    submesh_bottom: Any,
    left_space: fd.FunctionSpace,
    right_space: fd.FunctionSpace,
    bottom_space: fd.FunctionSpace,
    domain_length: float,
    transition_width: fd.Constant,
) -> list[fd.Function]:
    """Construct linear transition weights over each absorbing pad domain."""
    x_left, _ = fd.SpatialCoordinate(submesh_left)
    x_right, _ = fd.SpatialCoordinate(submesh_right)
    _, z_bottom = fd.SpatialCoordinate(submesh_bottom)

    distance_left = x_left
    distance_right = domain_length - x_right
    distance_top = domain_length - z_bottom

    weight_left_expr = fd.conditional(
        distance_left < transition_width,
        (transition_width - distance_left) / transition_width,
        0.0,
    )
    weight_right_expr = fd.conditional(
        distance_right < transition_width,
        (transition_width - distance_right) / transition_width,
        0.0,
    )
    weight_bottom_expr = fd.conditional(
        distance_top < transition_width,
        (transition_width - distance_top) / transition_width,
        0.0,
    )

    return [
        fd.Function(left_space).interpolate(weight_left_expr),
        fd.Function(right_space).interpolate(weight_right_expr),
        fd.Function(bottom_space).interpolate(weight_bottom_expr),
    ]

# %% [markdown]
# The next cell assembles the coupled mixed variational problem for one time step.
#
# It includes:
# - second-order time update and Laplacian on the parent domain;
# - one-way first-order equations on left/right/bottom pad domains;
# - interface constraints enforced with `EquationBC`;
# - a `LinearVariationalSolver` and the time-level fields (`u_nm1`, `u_n`, `u_np1`) used in the time loop.
#
# This structure follows the same Firedrake workflow as the FWI tutorial wave solver (`TrialFunction`, `TestFunction`, `LinearVariationalProblem`, `LinearVariationalSolver`) but extended to the HABC mixed system.

# %%
def wave_equation_solver(
    c: fd.Function,
    source_function: fd.Cofunction,
    dt: float,
    mixed_space: fd.FunctionSpace,
    dx0: fd.Measure,
    quad_rule0: Any,
) -> tuple[
    fd.LinearVariationalSolver,
    fd.Function,
    fd.Function,
    fd.Function,
    tuple[fd.Function, ...],
]:
    """Build and return the linear variational solver for one wave step."""
    u = fd.TrialFunction(mixed_space)
    v = fd.TestFunction(mixed_space)
    u_components = fd.split(u)
    v_components = fd.split(v)
    u0 = u_components[0]
    v0 = v_components[0]

    u_n = fd.Function(mixed_space)
    u_nm1 = fd.Function(mixed_space)
    u_np1 = fd.Function(mixed_space)
    u_n_components = u_n.subfunctions
    u_nm1_components = u_nm1.subfunctions
    u_n0 = u_n_components[0]
    u_nm10 = u_nm1_components[0]

    subspaces = [mixed_space.sub(1), mixed_space.sub(2), mixed_space.sub(3)]
    mesh = mixed_space.sub(0).mesh()
    submeshes = [space.mesh() for space in subspaces]
    c_subspaces = [
        fd.Function(space).interpolate(c, allow_missing_dofs=True)
        for space in subspaces
    ]
    u_n0_subspaces = [
        fd.Function(space).interpolate(u_n0, allow_missing_dofs=True)
        for space in subspaces
    ]

    m = 1 / (c * c)
    dt_const = fd.Constant(dt)
    dt2_const = fd.Constant(dt**2)
    dx0_rule = dx0(scheme=quad_rule0) if quad_rule0 is not None else dx0
    wave_form = (
        m * (u0 - 2.0 * u_n0 + u_nm10) / dt2_const * v0 * dx0_rule
        + fd.dot(fd.grad(u0), fd.grad(v0)) * dx0_rule
    )

    bcs = []
    direction_data = [(-1.0, 0), (1.0, 0), (1.0, 1)]
    for idx, (
        space,
        submesh,
        c_sub,
        (direction_sign, direction_axis),
    ) in enumerate(
        zip(subspaces, submeshes, c_subspaces, direction_data),
        start=1,
    ):
        u_i = u_components[idx]
        v_i = v_components[idx]
        u_n_i = u_n_components[idx]

        dx_i = fd.Measure(
            "dx",
            domain=submesh,
            intersect_measures=(fd.Measure("dx", mesh),),
        )
        ds_i_int = fd.Measure(
            "ds",
            domain=submesh,
            intersect_measures=(fd.Measure("dS", mesh),),
        )

        wave_form += (
            (1 / c_sub) * (u_i - u_n_i) / dt_const * v_i * dx_i
            + direction_sign * u_i.dx(direction_axis) * v_i * dx_i
        )

        interface_markers = get_interface_markers(mesh, submesh)
        if not interface_markers:
            raise ValueError(
                "No interface markers found between parent mesh and "
                f"submesh_{idx}"
            )

        interface_eq = (
            fd.inner(u_i - u0("+"), v_i) * ds_i_int(interface_markers)
            == fd.inner(fd.Constant(0.0), v_i) * ds_i_int(interface_markers)
        )
        bcs.append(
            fd.EquationBC(interface_eq, u_np1, interface_markers, V=space)
        )

    problem = fd.LinearVariationalProblem(
        fd.lhs(wave_form),
        fd.rhs(wave_form) + source_function,
        u_np1,
        bcs=bcs,
    )
    solver_parameters = {
        "mat_type": "matfree",
        "ksp_type": "gmres",
        "pc_type": "bjacobi",
        "ksp_rtol": 1.0e-8,
    }
    solver = fd.LinearVariationalSolver(
        problem,
        solver_parameters=solver_parameters,
    )
    return solver, u_np1, u_n, u_nm1, tuple(u_n0_subspaces)


# %% [markdown]
# After each solve, pad-domain solutions are merged into the parent field using transition weights. This creates a smooth handover between interior and absorbing regions and avoids sharp updates near interfaces.

# %%
def apply_habc_merging(
    parent_component: fd.Function,
    submesh_components: list[fd.Function],
    submesh_weights: list[fd.Function],
    mesh_weights: list[fd.Function],
    weighted_sums: list[fd.Function],
) -> None:
    """Merge pad-domain updates back into the parent solution component."""
    for weight_sub, u_sub, weighted_sum, weight_mesh in zip(
        submesh_weights,
        submesh_components,
        weighted_sums,
        mesh_weights,
    ):
        weighted_sum.interpolate(weight_sub * u_sub, allow_missing_dofs=True)
        weight_mesh.interpolate(weight_sub, allow_missing_dofs=True)
        parent_component.interpolate(
            (1.0 - weight_mesh) * parent_component + weighted_sum
        )

# %% [markdown]
# This final cell runs the full simulation workflow:
# - build mesh, extended pad domains, spaces, and quadrature;
# - construct source term and solver;
# - execute the time loop with `rhs_term` updates from `ricker_wavelet`;
# - apply HABC merging and shift time levels (`u_nm1 <- u_n <- u_np1`);
# - plot the final pressure solution.

# %%
"""Run the simulation and write the final pressure field to disk."""
simulation = SimulationConfig()

source_locations = np.asarray(simulation.source_locations, dtype=float)
source_location = tuple(source_locations[0])

boundary_distance = fd.Constant(simulation.boundary_distance)
mesh = fd.SquareMesh(
    simulation.nx,
    simulation.ny,
    simulation.domain_length,
    comm=fd.COMM_WORLD,
)
submesh_left, submesh_right, submesh_bottom, dx0 = submeshes(
    mesh,
    boundary_distance,
    simulation.domain_length,
    (
        simulation.left_marker,
        simulation.right_marker,
        simulation.bottom_marker,
    ),
)

parent_space = fd.FunctionSpace(mesh, "KMV", 1)
left_space = fd.FunctionSpace(submesh_left, "KMV", 1)
right_space = fd.FunctionSpace(submesh_right, "KMV", 1)
bottom_space = fd.FunctionSpace(submesh_bottom, "KMV", 1)
mixed_space = parent_space * left_space * right_space * bottom_space

quad_rule0 = finat.quadrature.make_quadrature(
    parent_space.finat_element.cell,
    parent_space.ufl_element().degree(),
    "KMV",
)
velocity = fd.Function(parent_space).interpolate(2.0)

source_term = build_source_term(
    mesh,
    parent_space,
    source_location,
)
rhs_term = fd.Cofunction(mixed_space.dual())
solver, u_np1, u_n, u_nm1, u_n0_subspaces = wave_equation_solver(
    velocity,
    rhs_term,
    simulation.dt,
    mixed_space,
    dx0,
    quad_rule0,
)

u_n0 = u_n.subfunctions[0]
parent_next = u_np1.subfunctions[0]
submesh_components = [
    u_np1.subfunctions[1],
    u_np1.subfunctions[2],
    u_np1.subfunctions[3],
]

submesh_weights = build_transition_weights(
    submesh_left,
    submesh_right,
    submesh_bottom,
    left_space,
    right_space,
    bottom_space,
    simulation.domain_length,
    boundary_distance,
)
mesh_weights = [fd.Function(parent_space) for _ in submesh_weights]
weighted_sums = [fd.Function(parent_space) for _ in submesh_weights]

for step in range(simulation.total_steps):
    print(f"Time step {step}/{simulation.total_steps - 1}")
    time = step * simulation.dt
    source_value = ricker_wavelet(time, simulation.frequency_peak)
    rhs_term.sub(0).assign(source_value * source_term)

    for u_n0_sub in u_n0_subspaces:
        u_n0_sub.interpolate(u_n0, allow_missing_dofs=True)

    solver.solve()
    apply_habc_merging(
        parent_component=parent_next,
        submesh_components=submesh_components,
        submesh_weights=submesh_weights,
        mesh_weights=mesh_weights,
        weighted_sums=weighted_sums,
    )

    u_nm1.assign(u_n)
    u_n.assign(u_np1)
        
if mesh.comm.size == 1 and mesh.comm.rank == 0:
    fig, ax = plt.subplots(figsize=(7, 4))
    contour = fd.tricontourf(parent_next, axes=ax, levels=40, cmap="viridis")
    fig.colorbar(contour, ax=ax, label="Pressure")
    ax.set_title("Final pressure field")
    ax.set_xlabel("x")
    ax.set_ylabel("z")
    plt.tight_layout()
    plt.show()
elif mesh.comm.rank == 0:
    print("Skipping plot in parallel run (requires a single-rank run for direct plotting).")
