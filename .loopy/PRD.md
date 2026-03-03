● List directory .
  └ 12 files found

✗ Check recent git history
  $ cd /Users/ddolci/dev_code/submesh_examples && git log --oneline -20 2>/dev/null
  Permission denied and could not request permission from user

● Read ruben_test.py
  └ 90 lines read

● Read acoustic_solver_submesh.py
  └ 210 lines read

● Read test_submesh_solve.py
  └ 1 line read

● Git log
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager log --oneline -20 2>&1 || echo "Not
   a git repo or no commits"
  └ 21 lines...

● Read test_submesh_solve.py lines 1-80
  └ 80 lines read

● Search boundary condition patterns
  $ cd /Users/ddolci/dev_code/submesh_examples && grep -n "clayton\|Clayton\|HABC\|habc\|hybrid\|abs
  orbing\|boundary\|submesh.*999\|submesh.*998\|indicator\|mark_entities\|x < \|x >"
  acoustic_solver_submesh.py | head -40
  └ 9 lines...

● Analyze boundary condition wiring
  $ cd /Users/ddolci/dev_code/submesh_examples && grep -n "ds1_ext\|ds_ext\|exterior_markers\|shared
  _exterior\|interface_markers\|DirichletBC\|weight\|transition\|w_sub\|w_mesh\|habc"
  acoustic_solver_submesh.py
  └ 21 lines...

Now I have a clear picture. Let me create the PRD.

✗ Create session directory
  $ mkdir -p /Users/ddolci/.copilot/session-state/e4be873f-ac2e-47fe-9b82-a4d0da0571a9
  Permission denied and could not request permission from user

● Create ~/.copilot/session-state/e4be873f-ac2e-47fe-9b82-a4d0da0571a9/plan.md (+88)

# PRD: Multi-boundary Clayton hybrid ABC with infinite-domain verification

## Problem Statement
The acoustic solver in `acoustic_solver_submesh.py` applies Clayton's hybrid absorbing boundary condition (HABC) only on the left boundary (x < 0.1 submesh), but it should be applied on the right, bottom, and top boundaries instead — and a reference "infinite domain" simulation is needed to verify that reflections are properly attenuated.

## Current Baseline
- **Submesh count**: 1 submesh covering x < 0.1 (line 122–124 of `acoustic_solver_submesh.py`), marker 999
- **Clayton ABC application**: Applied to all shared exterior markers of the single submesh (lines 95–98), which includes the x = 0 boundary — the boundary where it is explicitly not needed
- **HABC blending**: Single weight function ramping linearly from x = 0 to x = transition_width (0.1) (lines 158–165)
- **Domain**: UnitSquareMesh(80, 80), dt = 0.002, final_time = 1.0, frequency_peak = 7.0 (lines 116–118, 133)
- **Reflection verification**: None — no reference large-domain simulation exists for comparison
- **Boundary markers (Firedrake UnitSquareMesh convention)**: 1 = left (x = 0), 2 = right (x = 1), 3 = bottom (z = 0), 4 = top (z = 1)

## Goals
- G1: Create submeshes on the right (x > 0.9), bottom (z < 0.1), and top (z > 0.9) boundary strips and apply Clayton's hybrid ABC on each.
- G2: Remove Clayton's hybrid ABC from the x = 0 boundary (no submesh/HABC needed there).
- G3: Add a reference simulation on a sufficiently large domain where the wave never reaches the boundary, producing a reflection-free reference solution.
- G4: Compare the HABC solution against the reference solution to quantify reflection attenuation effectiveness.

## Non-Goals
- Adjoint/inversion workflows — this is forward-only.
- Changing the wave equation discretization (KMV elements, mass-lumping, time-stepping scheme).
- Optimizing performance or parallelism.
- Modifying existing test files (`test_submesh_*.py`).

## Users & Context
- Primary user: Computational acoustics researcher running Firedrake-based wave simulations.
- Environment: Python/Firedrake, local or HPC, sequential or MPI-parallel.

## Scope
- In scope:
  - Modify `acoustic_solver_submesh.py` to create 3 boundary submeshes (right, bottom, top) each with their own Clayton ABC terms.
  - Remove or skip the x < 0.1 submesh and its Clayton ABC.
  - Define appropriate indicator functions and markers (e.g., 997, 998, 999) for each boundary strip.
  - Construct per-boundary weight functions for HABC blending, oriented correctly (distance from the respective outer edge).
  - Create a reference solver run on a large domain (e.g., 5× or 10× larger) with the same source, velocity model, and time window, where the wave does not reach the far boundaries.
  - Compute and report an L2-norm (or max-norm) error between the HABC solution and the reference solution in the physical region of interest.
- Out of scope:
  - Corner treatment where two submeshes overlap (acceptable to leave as-is or use simple union).
  - Higher-order ABCs (e.g., Higdon, PML).
  - 3D extension.

## Data Sources
- N/A — problem is self-contained in code.

## Requirements
### Functional
- [F1] Create three submeshes via indicator functions: right boundary strip (x > 1 − δ), bottom strip (z < δ), top strip (z > 1 − δ), where δ is the absorbing layer thickness (currently 0.1).
- [F2] For each submesh, construct the Clayton first-order ABC surface integral `(1/c) * (∂u/∂t) * v * ds` on the shared exterior facets of that submesh with the parent mesh's outer boundary.
- [F3] For each submesh, apply a Dirichlet BC on the interface facets (submesh interior boundary) using the parent-mesh solution, as currently done for the left submesh.
- [F4] For each submesh, define a weight function that ramps from 1 at the outer boundary to 0 at the interface, oriented to the correct spatial direction.
- [F5] Blend HABC solutions into the parent-mesh solution using the weighted combination `u = (1 − w) * u_parent + w * u_submesh` for all three boundaries.
- [F6] Do NOT apply Clayton ABC or HABC blending on the x = 0 (left) boundary.
- [F7] Implement a reference simulation function that runs the same wave problem on a domain large enough (e.g., [0, 5] × [0, 5] with source at the same absolute position) that the wave does not reach any boundary within `final_time`.
- [F8] Compute and print/return the L2 error between the HABC solution and the reference solution restricted to the original [0, 1]² region.

### Non-Functional
- [N1] Performance: The multi-submesh solver should complete within ~3× the runtime of the current single-submesh solver for the same mesh resolution.
- [N2] Numerical stability: The divergence check mechanism (lines 37–67) must remain active and the solver must not diverge.
- [N3] Output: VTK output files for visualization of the HABC solution, reference solution, and error field.

## User Stories (MVP)
- As a researcher, I want Clayton hybrid ABCs on the right, bottom, and top boundaries so that spurious reflections are absorbed on all non-physical boundaries.
- As a researcher, I want the left boundary (x = 0) free of artificial absorbing conditions so that it can act as a physical (reflective or prescribed) boundary.
- As a researcher, I want to compare my HABC solution against an infinite-domain reference so that I can quantify the reflection attenuation quality.

## Success Metrics
- SM1: The HABC solver runs to completion (500 steps at dt = 0.002, final_time = 1.0) without divergence.
- SM2: The L2 relative error between the HABC solution and the reference solution (in the [0.2, 0.8]² interior region, avoiding boundary layers) is below 5% at final_time.
- SM3: VTK outputs are produced for both the HABC and reference simulations enabling visual comparison.

## Risks & Mitigations
- **Corner overlap**: Where two boundary submeshes meet (e.g., right + top corner), double-blending may occur → Mitigation: Use `min(w_total, 1.0)` or additive clamping for overlapping weights.
- **Reference domain size**: If the domain is too small, the wave reaches the boundary → Mitigation: Estimate wavefront travel distance as `c_max * final_time` (≈ 2.0 × 1.0 = 2.0 units) and size the domain to at least 3× that in each direction from the source.
- **Mesh resolution mismatch**: The reference large-domain mesh may have different resolution → Mitigation: Use the same `h` (element size) as the original mesh, only increase domain extents.
- **Mixed function space complexity**: Adding 3 more submesh function spaces to the mixed space `V = V0 * V1 * V2 * V3 * V4` increases solver complexity → Mitigation: Consider solving each submesh Clayton problem independently rather than in a single monolithic mixed system.

## Open Questions
- Q1: Should corner cells (where two absorbing strips overlap) belong to one submesh, both, or a dedicated corner submesh?
- Q2: What boundary condition should be applied at x = 0 — free-surface (Neumann, natural BC) or hard-wall (Dirichlet u = 0)?
- Q3: Is the current absorbing strip thickness δ = 0.1 (10% of domain) adequate for frequency_peak = 7.0, or should it be tuned?

## Assumptions
- A1: Firedrake supports multiple independent submeshes from the same parent mesh with distinct markers — `ruben_test.py` (lines 69–75) already demonstrates two submeshes (markers 999 and 998), confirming this is supported.
- A2: The UnitSquareMesh Firedrake boundary markers follow the convention: 1 = left, 2 = right, 3 = bottom, 4 = top.
- A3: The x = 0 boundary should have a natural (Neumann) boundary condition (no surface integral term), which is the default when no BC is specified on that boundary.
- A4: A reference domain of [0, 5] × [0, 5] with source at (0.3, 0.1) absolute coordinates is large enough that with c_max ≈ 2.0 and final_time = 1.0, the wavefront (traveling ≈ 2.0 units) does not reach any boundary (minimum distance to boundary is 3.0 units from source).
