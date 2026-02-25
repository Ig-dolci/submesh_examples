---
agent_command: copilot --allow-all
test_command: pytest test_submesh_acoustic.py
max_iterations: 50
max_minutes: 120
backoff_ms: 5000
rotate_bytes: 150000
git:
  branch: main
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
- [F5] Freeze `solve_acoustic_submesh(...)` compatibility:
  - Required call arguments remain `mesh`, `source`, `wave_speed`, `dt`, `t_end`, `boundary_labels` (no new required parameters).
  - Return value remains a `dict` with keys: `mesh`, `extended_submesh`, `extended_domain_label`, `interior_submesh`, `interior_domain_label`, `source`, `wave_speed`, `dt`, `t_end`, `boundary_labels`, `clayton_labels`, `interface_label`, `num_steps`, `solution`, `solution_norm`.
  - `boundary_labels`, `clayton_labels`, and `interface_label` remain tuple-valued diagnostics.
  - Non-2D meshes continue to raise `ValueError` containing `mesh.topological_dimension() must be 2`.
- [F6] Add deterministic tests for Clayton-vs-reflective norm behavior.

#### Non-Functional
- [N1] CI-scale inversion smoke run should complete within 300 seconds.
- [N2] No outbound data transfer; data handling remains local/in-memory by default.
- [N3] Keep API script-friendly with clear docstrings and reproducible defaults.

### Success Metrics
- Optimization convergence: `J_final <= 0.8 * J_initial` within at most 20 iterations, with stop criteria `ftol=1e-3`, `J <= 1e-8`, or `max_iter=20`.
- Boundary consistency: `solution_norm(clayton) <= solution_norm(reflective)` for equivalent setup.
- Compatibility: acoustic test module passes without breaking existing call signatures.

### Risks & Mitigations
- Runtime instability in tests: keep small smoke-scale defaults.
- Boundary regressions: add explicit assertions for label partitioning.

### Confirmed MVP Decisions
- Source parallelism: use a single-source sequential loop for MVP; defer `Ensemble` source parallelism.
- Optimizer stopping: stop on first of `ftol=1e-3` relative objective change, `J <= 1e-8`, or `max_iter=20`.
- Observed data source: synthetic observed data only for MVP.

### Assumptions
- Scope remains 2D-only.
- Existing boundary semantics are authoritative.

## Phase: plan
<!-- loopy:phase plan -->

- [x] Confirm final acceptance criteria for MVP (including optimizer stop criteria and source parallelism decision).
- [x] Freeze API compatibility constraints for `solve_acoustic_submesh(...)`.
- [x] Finalize test matrix for boundary semantics.

### Finalized boundary semantics test matrix
- Shared setup for deterministic boundary checks: `RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True)`, `source=1.0`, `wave_speed=1.0`, `dt=0.01`.

| Case | `boundary_labels` input | Expected `interface_label` | Expected `clayton_labels` | Deterministic assertions |
| --- | --- | --- | --- | --- |
| BM-1 | `(1, 2, 3, 4)` | `(5,)` | `(2, 3, 4)` | Interface marker is excluded from Clayton labels; one-step solve (`t_end=0.01`) returns finite norm. |
| BM-2 | `(5,)` | `(5,)` | `()` | Pure interface-only run is reflective (no Clayton damping). |
| BM-3 | `(2, 3, 4)` | `(5,)` | `(2, 3, 4)` | Clayton damping applies on outer non-interface labels and satisfies `solution_norm(BM-3) <= solution_norm(BM-2)` for `t_end=0.2`. |
| BM-4 | `(2, 5, 99)` | `(5,)` | `(2,)` | Unknown label `99` and interface label `5` are both excluded from Clayton damping. |
| BM-5 | `()` | n/a | n/a | Raises `ValueError` containing `boundary_labels must contain at least one label.` |
| BM-6 | `"bad_string"` | n/a | n/a | Raises `TypeError` containing `boundary_labels must be an iterable of labels, not a string.` |

## Phase: implement
<!-- loopy:phase implement -->

- [x] Add a forward-style objective/optimization entry point in `acoustic_solver.py` while keeping `solve_acoustic_submesh(...)` required args and return keys unchanged.
- [x] Preserve boundary partition semantics in `acoustic_solver.py`: `interface_label` inferred from submesh-only markers and `clayton_labels` filtered to user labels on outer non-interface markers.
- [x] Expand `test_submesh_acoustic.py` to implement matrix cases BM-1..BM-6, including mixed-label filtering and Clayton-vs-reflective norm ordering.

## Phase: verify
<!-- loopy:phase verify -->

- [x] Run `pytest test_submesh_acoustic.py`.
- [x] Validate BM-1..BM-6 boundary assertions, including mixed-label filtering `(2, 5, 99) -> clayton_labels == (2,)` and invalid-input errors for `()` and `"bad_string"`.
- [x] Confirm reflective-vs-Clayton norm ordering (`solution_norm((2, 3, 4)) <= solution_norm((5,))`) and existing API-focused acoustic tests remain green.
