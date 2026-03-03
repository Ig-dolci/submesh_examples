# Loopy Hints

## Findings from implement

### What was investigated
- Implemented all five implement-phase tasks: dual submesh construction (right x>0.9, bottom z<0.1), per-submesh Clayton ABC wiring, oriented weight blending with corner clamping, large-domain reference solver, and L2 error computation.

### What was found
- The solver structure in `wave_equation_solver()` already supported N submeshes via the mixed space `V = V0 * V1_right * V1_bottom` pattern.
- Weight functions for right (`(x - 0.9)/0.1`) and bottom (`(0.1 - z)/0.1`) boundary strips implemented with additive clamping for corner overlap.
- Reference solver uses [-2,3]×[-2,3] domain (400×400 mesh, same h=1/80), giving >2.1 unit clearance from source to all boundaries.
- L2 error computation restricts to [0.2,0.8]² interior to avoid boundary layer artifacts, using `interpolate(u_ref, allow_missing_dofs=True)` for cross-mesh transfer.

### Conclusion
All implementation tasks are complete. The code should run end-to-end: HABC solve → reference solve → error computation → VTK outputs.

### Recommended next action
Run `python3 acoustic_solver_submesh.py` to verify no divergence, check that outputs are generated, and confirm the error metric is reported.

### What was investigated
- Read `acoustic_solver_submesh.py` (210 lines): current solver structure, submesh creation, Clayton ABC wiring, HABC blending, time loop.
- Read `ruben_test.py` (90 lines): confirmed Firedrake supports multiple submeshes from same parent mesh with distinct markers (999, 998).
- Read `.loopy/PRD.md`: full requirements, goals, risks, success metrics.

### What was found
1. **Single left-side submesh**: `indicator_function = conditional(x < 0.1, 1, 0)` with marker 999 (line 122). This creates an absorbing strip on the LEFT boundary (x=0), but per PRD G2, the left boundary should NOT have ABC.
2. **`wave_equation_solver()` is monolithic**: It builds one mixed space `V = V0 * V1` and one Clayton term. To support N submeshes, this needs to either (a) extend to `V = V0 * V1 * V2 * ... * VN` or (b) solve each submesh Clayton problem independently and blend results.
3. **Approach (b) is simpler**: Each submesh can have its own independent Clayton solve (TrialFunction/TestFunction on its own V_sub), coupled to parent via Dirichlet BCs. This avoids a large monolithic mixed system. The current code already does most of this — just needs to be looped.
4. **Weight function orientation**: Current weight ramps from x=0 outward: `(transition_width - x_sub) / transition_width`. For right boundary, it should ramp from x=1 inward: `(x_sub - (1-δ)) / δ`. For bottom, from z=0 upward: `(δ - z_sub) / δ`.
5. **Reference domain**: With c_max ≈ 2.0 and final_time = 1.0, wave travels ~2.0 units. A [0,5]×[0,5] domain with source at (0.3,0.1) has min distance to boundary of ~0.1 (bottom). Need to shift source or use [-2,3]×[-2,3] to ensure sufficient clearance. Actually, at z=0.1 and c_max=2.0, the wave reaches z=0 in 0.05s — the reference domain must be larger or the source placed further from boundaries. Using [−2, 3] × [−2, 3] with source at (0.3, 0.1) gives ≥2.1 units clearance in all directions.
6. **Corner overlap**: Where right strip (x>0.9) and bottom strip (z<0.1) overlap (the [0.9,1]×[0,0.1] corner), both weights are nonzero. Clamping `min(w_right + w_bottom, 1.0)` handles this.

### Conclusion
The implementation requires: (1) replacing the single left submesh with right+bottom submeshes, (2) running independent Clayton solves per submesh, (3) blending with correctly oriented weight functions, and (4) adding a large-domain reference solver for verification. The `ruben_test.py` pattern confirms multi-submesh is already supported.

### Recommended next action
Implement the changes in order: submesh construction → per-submesh Clayton wiring → blending → reference solver → error computation.
