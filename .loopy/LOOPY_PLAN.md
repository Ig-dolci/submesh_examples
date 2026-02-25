---
agent_command: copilot
test_command: pytest -q test_submesh_acoustic.py
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
  test_command: pytest -q test_submesh_acoustic.py
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
    test_command: pytest -q test_submesh_acoustic.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Scope
  - section: Requirements
---

# Plan

Objective: deliver a clean 2D acoustic solver path using `RectangleMesh` while preserving current output contract and coupling behavior.

## Phase: plan
<!-- loopy:phase plan -->

- [x] Confirm current target files: `acoustic_solver.py` and `test_submesh_acoustic.py`.
- [x] Confirm scope boundaries: acoustic module and dedicated acoustic tests only.
- [ ] Finalize API decision: canonical name (`acoustic_solve`) and compatibility wrapper (`solve_acoustic_submesh`).
- [ ] Finalize 2D mesh defaults for tests (`nx`, `ny`, `Lx`, `Ly`) and required boundary labels.
- [ ] Lock acceptance criteria for preserved diagnostics: `solution_norm`, `interface_label`, `clayton_labels`, `num_steps`.

Acceptance:
- Phase complete when API and mesh conventions are explicit and testable.

## Phase: implement
<!-- loopy:phase implement -->

- [ ] Refactor `acoustic_solver.py` to explicit imports (remove wildcard import).
- [ ] Ensure primary 2D path uses `RectangleMesh(nx, ny, Lx, Ly, quadrilateral=True)`.
- [ ] Enforce 2D mesh validation with clear error messaging.
- [ ] Preserve output contract and submesh/interface coupling semantics.
- [ ] Add/update docstrings for public entry points and non-trivial helpers.
- [ ] Keep backward-compatible call surface via alias/wrapper if API name changes.

Acceptance:
- Phase complete when static checks show expected symbols/usages and implementation matches PRD functional requirements.

## Phase: verify
<!-- loopy:phase verify -->

- [ ] Run targeted tests: `pytest -q test_submesh_acoustic.py`.
- [ ] Verify no regression in return diagnostics and key behavior assertions.
- [ ] Run focused grep checks:
  - [ ] `rg "from firedrake import \*" acoustic_solver.py` returns no matches.
  - [ ] `rg "RectangleMesh" acoustic_solver.py test_submesh_acoustic.py` returns expected matches.
  - [ ] `rg "UnitIntervalMesh" acoustic_solver.py` has no primary-path dependency.
- [ ] Document any environment limitations (if runtime execution is blocked) and defer final runtime gate to CI.

Acceptance:
- Phase complete when targeted tests pass locally, or CI gate is explicitly identified when local execution is unavailable.