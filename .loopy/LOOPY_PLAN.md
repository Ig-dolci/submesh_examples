---
agent_command: copilot --allow-all
test_command: python3 acoustic_solver_submesh.py
max_iterations: 50
max_minutes: 120
backoff_ms: 5000
rotate_bytes: 150000
git:
  branch: ''
  commit: true
  commit_message: 'loopy: {change_type} {task_summary}'
phase_defaults:
  stop_on: all_checked
  test_command: python3 acoustic_solver_submesh.py
phases:
  - id: plan
    title: Plan
    stop_on: all_checked
  - id: implement
    title: Implement
    stop_on: all_checked
  - id: verify
    title: Verify
    stop_on:
      - all_checked
      - tests_pass
    test_command: python3 acoustic_solver_submesh.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

## PRD: Multi-boundary Clayton hybrid ABC with infinite-domain verification

### Problem Statement
The acoustic solver in `acoustic_solver_submesh.py` currently targets a single absorbing strip. The goal is to support right and bottom absorbing boundaries with interface consistency and verify quality against an effectively reflection-free reference run.

### Current Baseline
- Single absorbing submesh and one blending ramp.
- Interface continuity handled with submesh-side Dirichlet projection.
- No explicit reference-domain validation in this plan file.

### Goals
- Add Clayton HABC on right and bottom boundary strips.
- Keep inside interface Dirichlet constraints on each submesh interface.
- Compare against a large-domain reference solution.

### Non-Goals
- No adjoint/inversion changes.
- No change to core time discretization.
- No 3D extension in this iteration.

### Functional Requirements
- [ ] Build two absorbing strips: right (`x > 1-δ`), bottom (`z < δ`).
- [ ] Apply Clayton boundary term only on strip facets shared with parent exterior.
- [ ] Keep interface Dirichlet coupling for each strip.
- [ ] Blend strip and parent solutions with boundary-oriented weights.
- [ ] Add large-domain reference and compute error in the physical ROI.

### Non-Functional Requirements
- [ ] Preserve runtime stability (divergence checks active).
- [ ] Keep runtime within acceptable overhead of baseline.
- [ ] Produce VTK outputs for HABC, reference, and error fields.

### Risks
- Overlap at strip corners can double-count blending.
- Reference domain size/resolution can bias error estimate.

## Phase: plan
<!-- loopy:phase plan -->
- [ ] Plan scope, goals, and constraints documented.

## Phase: implement
<!-- loopy:phase implement -->
- [ ] Add multi-strip submesh construction.
- [ ] Add per-strip Clayton and interface Dirichlet wiring.
- [ ] Add weighted blending and corner handling.
- [ ] Add reference-run function and error metrics.

## Phase: verify
<!-- loopy:phase verify -->
- [ ] Run `python3 acoustic_solver_submesh.py`.
- [ ] Confirm no divergence and outputs generated.
- [ ] Confirm reference comparison metric is reported.
