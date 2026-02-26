---
agent_command: copilot --allow-all
test_command: pytest test_acoustic_solver.py
max_iterations: 50
max_minutes: 240
backoff_ms: 5000
rotate_bytes: 150000
git:
  branch: ''
  commit: true
  commit_message: 'loopy: {change_type} {task_summary}'
phase_defaults:
  stop_on: all_checked
  test_command: pytest test_acoustic_solver.py
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
    test_command: pytest test_acoustic_solver.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

## PRD: Forward Acoustic Wave Solver on Submesh with Hybrid A1 Clayton Boundaries

### Problem Statement
Implement a second-order acoustic forward solver in Firedrake, using submeshes to represent physical and extended domains and applying Hybrid A1 Clayton absorbing boundary treatment on the outer extended boundaries.

### Current Baseline
- The current repository focuses on submesh mechanics and test patterns.
- A dedicated active acoustic solver and acoustic tests are not currently present in the working tree.

### Goals
- Add a forward-only second-order acoustic wave solver path.
- Use submesh construction consistent with existing repository patterns.
- Apply A1 Clayton on outer extended boundaries while preserving physical/extended interface behavior.
- Keep implementation compatible with Firedrake tutorial-style source forcing (Ricker wavelet, forward modeling workflow).

### Non-Goals
- Full waveform inversion optimization loop.
- Adjoint/gradient workflow for MVP.
- Unrelated refactors in existing submesh tests.

### Users & Context
- Primary users: Firedrake developers and researchers validating absorbing-boundary behavior.
- Execution context: Python/Firedrake with pytest.

### Scope
- In scope:
  - Forward wave equation time-stepping implementation.
  - Submesh partitioning of physical and extension regions.
  - Hybrid A1 Clayton boundary handling on eligible outer boundaries.
  - Minimal deterministic tests for API and boundary behavior.
- Out of scope:
  - Inversion, optimization, and production-scale workflows.

### Requirements
#### Functional
- [F1] Provide a callable forward solver entry point for second-order acoustic propagation.
- [F2] Implement source-time term compatible with tutorial-style Ricker forcing.
- [F3] Build and use physical + extended domains with `Submesh`.
- [F4] Apply Clayton A1 only on non-interface outer boundaries of the extended domain.
- [F5] Return diagnostics needed by tests (final field and scalar metrics).

#### Non-Functional
- [N1] Small tests should run quickly in CI-scale settings.
- [N2] No outbound I/O or external dependencies at runtime.
- [N3] Scriptable, deterministic API for automated pytest checks.

### Success Metrics
- Solver module and tests are importable and executable in the repository.
- Tests confirm finite outputs, stable boundary labeling, and expected reflective-vs-Clayton trend.

### Risks & Mitigations
- Weak-form ambiguity for A1 details -> encode assumptions directly in implementation and tests.
- Boundary-label mismatch risk -> validate label partitioning in tests.

### Open Questions
- Keep MVP strictly single-source loop first, then extend to multi-source.
- Confirm accepted stopping/diagnostic criteria for any optional iterative wrappers.

### Assumptions
- MVP is 2D first.
- Existing submesh examples define preferred mesh-labeling and measure patterns.

## Phase: plan
<!-- loopy:phase plan -->

- [ ] Validate target solver API and file names.
- [ ] Confirm label strategy for interface and outer Clayton boundaries.

## Phase: implement
<!-- loopy:phase implement -->

- [ ] Implement second-order acoustic forward solver with Ricker source.
- [ ] Implement hybrid A1 Clayton treatment on extended-domain outer boundaries.
- [ ] Wire submesh physical/extended domain setup using existing patterns.
- [ ] Add focused acoustic tests for finite outputs and boundary behavior.

## Phase: verify
<!-- loopy:phase verify -->

- [ ] Run `pytest test_acoustic_solver.py`.
- [ ] Verify boundary partition and reflective-vs-Clayton comparison assertions.
