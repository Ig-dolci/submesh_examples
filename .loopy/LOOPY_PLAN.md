---
agent_command: copilot --allow-all
test_command: pytest test_submesh_acoustic.py
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
  test_command: pytest test_submesh_acoustic.py
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
    test_command: pytest test_submesh_acoustic.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

## PRD: Forward-Style Submesh Acoustic Solver with Clayton BC

### Problem Statement
Implement a Firedrake solver workflow aligned with the forward solver of the Full-Waveform Inversion (FWI) demo while preserving this project’s submesh-based extended-domain Clayton absorbing boundary condition behavior.

### Current Baseline
- Solver module: `acoustic_solver.py` exposes `acoustic_solve` and `solve_acoustic_submesh`.
- Existing tests include `test_submesh_acoustic.py` and verify baseline submesh acoustic behavior.

### Goals
- Add a forward solve.
- Preserve extended-domain submesh construction and Clayton A1 behavior on non-interface outer boundaries.
- Keep backward compatibility for existing acoustic API usage and diagnostics.

### Non-Goals
- Rework unrelated submesh modules/tests.
- Add 3D inversion support.
- FWI inversion workflow (gradient, optimizer) in this phase.
- Build production-scale data pipelines.

### Users & Context
- Firedrake users prototyping inversion with submesh coupling.
- CI maintainers protecting acoustic/submesh regressions.

### Scope
- In scope:
  - Forward-style objective and optimization workflow.
  - Retain submesh split and boundary semantics (`interface_label`, `clayton_labels`).
  - Add tests for boundary invariants.
- Out of scope:
  - GUI/visualization features.
  - External data ingestion pipelines.

### Requirements
#### Functional
- [F1] Provide a forward solver entry point with forward modeling.
- [F2] Include Ricker-like source-time behavior and support multiple sources/receivers.
- [F3] Preserve current submesh construction and Clayton damping semantics (exclude interface boundaries).
- [F4] Preserve diagnostics (`interface_label`, `clayton_labels`).
- [F5] Keep `solve_acoustic_submesh(...)` callable with existing argument shape and return keys required by tests.
- [F6] Add deterministic tests for Clayton-vs-reflective norm behavior.

#### Non-Functional
- [N1] CI-scale inversion smoke run should complete within 300 seconds.
- [N2] No outbound data transfer; data handling remains local/in-memory by default.
- [N3] Keep API script-friendly with clear docstrings and reproducible defaults.

### Success Metrics
- Boundary consistency: `solution_norm(clayton) <= solution_norm(reflective)` for equivalent setup.
- Compatibility: acoustic test module passes without breaking existing call signatures.

### Risks & Mitigations
- Runtime instability in tests: keep small smoke-scale defaults.
- Boundary regressions: add explicit assertions for label partitioning.

### Open Questions
- MVP source parallelism now (`Ensemble`) or single-source loop first?
single-source loop first.
- Synthetic observed data only for MVP, or file-driven observed data needed now?
Synthetic observed data only for MVP.

### Assumptions
- Scope remains 2D-only.
- Existing boundary semantics are authoritative.

## Phase: plan
<!-- loopy:phase plan -->

- [ ] Confirm final acceptance criteria for MVP (including optimizer stop criteria and source parallelism decision).
- [ ] Freeze API compatibility constraints for `solve_acoustic_submesh(...)`.
- [ ] Finalize test matrix for and boundary semantics.

## Phase: implement
<!-- loopy:phase implement -->

- [ ] Add forward solver entry point in `acoustic_solver.py`.
- [ ] Preserve existing submesh and Clayton boundary behavior; keep current API contract stable.
- [ ] Add/adjust tests in `test_submesh_acoustic.py` for boundary invariants.

## Phase: verify
<!-- loopy:phase verify -->

- [ ] Run `pytest test_submesh_acoustic.py`.
- [ ] Validate objective trend and Clayton-vs-reflective norm assertions.
- [ ] Confirm no regressions in existing API-based tests.
