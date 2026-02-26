---
agent_command: copilot
test_command: pytest test_acoustic_solver.py
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

<!-- loopy:seed ● List directory .
  └ 15 files found

● Read instruction_loopy.text
  └ 8 lines read

● Show recent commits
  $ git --no-pager log --oneline -20
  └ 21 lines...

● SQL: Create and start todos
  └ 3 row(s) inserted. Last inserted row ID: 3.

● Glob "**/*acoustic*" in /Users/ddolci/dev_code/submesh_examples
  └ 56 files found

● Grep "Submesh|clayton|Clayton|absorbing|extended
domain|A1|physical|interface_label|clayton_labels" (/Users/ddolci/dev_code/submesh_examples)
  └ 64 lines found

● Read acoustic_solver.py
  └ 89 lines read

● Read test_submesh_solve.py lines 400-560
  └ 161 lines read

● Glob "**/test*acoustic*.py" in /Users/ddolci/dev_code/submesh_examples
  └ No matches found

✗ Count VTU snapshots
  $ python - <<'PY'
  import glob
  print(len(glob.glob('acoustic_solution/acoustic_solution_*.vtu')))
  PY
  Permission denied and could not request permission from user

● Grep "Submesh" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Grep "Clayton|clayton|absorbing|A1" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Show acoustic_solver commit history
  $ git --no-pager log --oneline -- acoustic_solver.py | head -20
  └ 19 lines...

● Grep "dt\s*=|final_time\s*=|frequency_peak\s*=|total_steps\s*=|if step % 10 == 0"
(/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 5 lines found

● Check tracked acoustic files
  $ git --no-pager status --short && git --no-pager ls-files | rg
  'acoustic|submesh_acoustic|test_acoustic'
  └ 63 lines...

● Read test_submesh_solve.py lines 429-465
  └ 35 lines read

● Read test_submesh_assign.py lines 1-80
  └ 80 lines read

● Read test_submesh_basics.py
  └ 16 lines read

● Todo started: inspect-code

● Todo queried:

● Todo completed: write-prd

● Todo queried:

# PRD: Extended-Domain Acoustic Solver with Submesh and Clayton A1 ABC

## Problem Statement
`acoustic_solver.py` currently solves on a single domain without Submesh-based physical/extended partitioning or Clayton A1 absorbing boundaries, so it does not implement the requested extended-domain boundary treatment.

## Current Baseline
- Submesh usage in `acoustic_solver.py`: **0 matches** for `Submesh` (source: `rg` count on `acoustic_solver.py`).
- Clayton/absorbing boundary implementation in `acoustic_solver.py`: **0 matches** for `Clayton|clayton|absorbing|A1` (source: `rg` count on `acoustic_solver.py`).
- Current solver setup is single-domain: `UnitSquareMesh(80, 80)`, `dt=0.002`, `final_time=1.0`, `frequency_peak=7.0`, `total_steps=int(final_time/dt)+1`, output every 10 steps (source: `view`/`rg -n` on `acoustic_solver.py`).
- Existing output artifacts: **51 VTK snapshots** (`acoustic_solution_0.vtu` … `acoustic_solution_50.vtu`) indicating current run behavior (source: `glob` on `acoustic_solution/acoustic_solution_*.vtu`).

## Goals
- Add Submesh-based decomposition for physical and extended domains in `acoustic_solver.py`.
- Implement Clayton A1 absorbing boundary condition on the extended-domain outer boundary while preserving the core wave equation form.

## Non-Goals
- Rewriting the interior acoustic PDE discretization beyond boundary-condition-coupling needs.
- Building inversion/adjoint/optimization workflows.
- Refactoring unrelated submesh example tests.

## Users & Context
- Primary user: numerical PDE developer running Firedrake-based acoustic experiments from this repository.
- Secondary user(s): maintainers validating submesh coupling patterns against existing `test_submesh_*` references.
- Environment: internal Python/Firedrake research codebase, CLI/pytest workflow.

## Scope
- In scope:
  - Create physical vs extended region labeling and construct corresponding `Submesh` objects.
  - Add interface and outer-boundary terms needed for Clayton A1 behavior.
  - Keep current source injection/time-stepping workflow semantics unless boundary implementation requires minimal changes.
  - Add/adjust focused verification for boundary behavior and Submesh construction.
- Out of scope:
  - New mesh generators beyond what Firedrake already provides in this repo.
  - Performance optimization unrelated to correctness.
  - Visualization/post-processing redesign.

## Data Sources
- `acoustic_solver.py`: current solver structure, parameters, and weak form implementation (`view`, `rg`).
- `instruction_loopy.text`: requested behavior (extended domain + Submesh + Clayton A1).
- `test_submesh_*.py` (especially `test_submesh_solve.py`, `test_submesh_assign.py`, `test_submesh_basics.py`): reference Submesh/RelabeledMesh/interface-measure patterns (`view`, `rg`).
- Git history: `git log --oneline -20` and `git log --oneline -- acoustic_solver.py` for recent behavior expectations and potential regression context.
- Generated artifacts: `acoustic_solution/*.vtu` for immediate measurable output baseline (`glob`).

## Requirements
### Functional
- [F1] Partition a parent mesh into labeled physical and extended regions using Firedrake labeling (`DG0`/`RelabeledMesh`) and instantiate corresponding `Submesh` objects.
- [F2] Assemble forms so physical and extended solutions are coupled consistently across their interface using Submesh-compatible measures/intersections.
- [F3] Apply Clayton A1 absorbing boundary condition terms on selected outer boundary labels of the extended domain.
- [F4] Preserve existing interior wave equation update form and source forcing shape unless a boundary-term integration change is strictly required.
- [F5] Expose boundary-label selection explicitly (inputs or clearly defined constants) so behavior is deterministic and testable.
- [F6] Produce finite solution outputs for at least one full forward run with absorbing mode enabled.

### Non-Functional
- [N1] Performance: maintain current step loop viability (same order of timesteps and no catastrophic slowdown for current mesh size).
- [N2] Security/Privacy: no external data transfer; all computation remains local code/data.
- [N3] Accessibility: N/A for UI; maintain clear function naming/docstrings and deterministic CLI-testability.

## User Stories (MVP)
- As a Firedrake developer, I want to run the acoustic solver on physical+extended Submeshes so that absorbing boundaries can be modeled without changing interior physics.
- As a maintainer, I want a deterministic way to select Clayton boundary labels so that I can test reflective vs absorbing behavior reliably.
- As a researcher, I want output fields from an absorbing-boundary run to remain finite and stable over the configured simulation time.

## Success Metrics
- `acoustic_solver.py` contains Submesh-based physical/extended domain construction and no longer has zero Submesh references (target: `rg "Submesh" acoustic_solver.py` > 0).
- Clayton A1 boundary logic is present and selectable (target: boundary-condition code path exists and is exercised by tests).
- Forward-run smoke test passes with absorbing mode and returns finite norm(s) over the configured horizon.
- Regression check: existing relevant submesh tests used as references remain green for untouched behavior.

## Risks & Mitigations
- Incorrect region/interface labeling → Reuse proven `RelabeledMesh` + `Submesh` patterns from `test_submesh_solve.py` and assert label consistency.
- Boundary-term sign or facet selection errors → Add focused tests comparing absorbing vs reflective boundary outcomes.
- Drift from intended API/history → Use recent `git log` expectations as guidance and document any deliberate API deviations.

## Open Questions
- Which boundary labels are the canonical targets for Clayton A1 in this project’s intended mesh setup (all non-interface outer labels vs explicit subset)?
- Should absorbing-vs-reflective behavior be controlled via function arguments, config constants, or both?
- Is preserving legacy `solve_acoustic_submesh(...)` API compatibility required in addition to updating `main()` flow?

## Assumptions
- The requested change is a feature completion for the current working tree, where `acoustic_solver.py` currently lacks Submesh/Clayton implementation (directly evidenced by file contents and searches).
- Existing `test_submesh_*` files are the authoritative in-repo reference for Submesh semantics because no active `test_acoustic_solver.py` is present in the current tree.
- Measurable physics acceptance will be based on deterministic finite-run checks and relative absorbing-vs-reflective behavior, not external benchmark datasets (none found in repo). -->

## Phase: plan
<!-- loopy:phase plan -->

- [ ] Plan: [needs refinement] ● List directory .
  └ 15 files found

● Read instruction_loopy.text
  └ 8 lines read

● Show recent commits
  $ git --no-pager log --oneline -20
  └ 21 lines...

● SQL: Create and start todos
  └ 3 row(s) inserted. Last inserted row ID: 3.

● Glob "**/*acoustic*" in /Users/ddolci/dev_code/submesh_examples
  └ 56 files found

● Grep "Submesh|clayton|Clayton|absorbing|extended
domain|A1|physical|interface_label|clayton_labels" (/Users/ddolci/dev_code/submesh_examples)
  └ 64 lines found

● Read acoustic_solver.py
  └ 89 lines read

● Read test_submesh_solve.py lines 400-560
  └ 161 lines read

● Glob "**/test*acoustic*.py" in /Users/ddolci/dev_code/submesh_examples
  └ No matches found

✗ Count VTU snapshots
  $ python - <<'PY'
  import glob
  print(len(glob.glob('acoustic_solution/acoustic_solution_*.vtu')))
  PY
  Permission denied and could not request permission from user

● Grep "Submesh" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Grep "Clayton|clayton|absorbing|A1" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Show acoustic_solver commit history
  $ git --no-pager log --oneline -- acoustic_solver.py | head -20
  └ 19 lines...

● Grep "dt\s*=|final_time\s*=|frequency_peak\s*=|total_steps\s*=|if step % 10 == 0"
(/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 5 lines found

● Check tracked acoustic files
  $ git --no-pager status --short && git --no-pager ls-files | rg
  'acoustic|submesh_acoustic|test_acoustic'
  └ 63 lines...

● Read test_submesh_solve.py lines 429-465
  └ 35 lines read

● Read test_submesh_assign.py lines 1-80
  └ 80 lines read

● Read test_submesh_basics.py
  └ 16 lines read

● Todo started: inspect-code

● Todo queried:

● Todo completed: write-prd

● Todo queried:

# PRD: Extended-Domain Acoustic Solver with Submesh and Clayton A1 ABC

## Problem Statement
`acoustic_solver.py` currently solves on a single domain without Submesh-based physical/extended partitioning or Clayton A1 absorbing boundaries, so it does not implement the requested extended-domain boundary treatment.

## Current Baseline
- Submesh usage in `acoustic_solver.py`: **0 matches** for `Submesh` (source: `rg` count on `acoustic_solver.py`).
- Clayton/absorbing boundary implementation in `acoustic_solver.py`: **0 matches** for `Clayton|clayton|absorbing|A1` (source: `rg` count on `acoustic_solver.py`).
- Current solver setup is single-domain: `UnitSquareMesh(80, 80)`, `dt=0.002`, `final_time=1.0`, `frequency_peak=7.0`, `total_steps=int(final_time/dt)+1`, output every 10 steps (source: `view`/`rg -n` on `acoustic_solver.py`).
- Existing output artifacts: **51 VTK snapshots** (`acoustic_solution_0.vtu` … `acoustic_solution_50.vtu`) indicating current run behavior (source: `glob` on `acoustic_solution/acoustic_solution_*.vtu`).

## Goals
- Add Submesh-based decomposition for physical and extended domains in `acoustic_solver.py`.
- Implement Clayton A1 absorbing boundary condition on the extended-domain outer boundary while preserving the core wave equation form.

## Non-Goals
- Rewriting the interior acoustic PDE discretization beyond boundary-condition-coupling needs.
- Building inversion/adjoint/optimization workflows.
- Refactoring unrelated submesh example tests.

## Users & Context
- Primary user: numerical PDE developer running Firedrake-based acoustic experiments from this repository.
- Secondary user(s): maintainers validating submesh coupling patterns against existing `test_submesh_*` references.
- Environment: internal Python/Firedrake research codebase, CLI/pytest workflow.

## Scope
- In scope:
  - Create physical vs extended region labeling and construct corresponding `Submesh` objects.
  - Add interface and outer-boundary terms needed for Clayton A1 behavior.
  - Keep current source injection/time-stepping workflow semantics unless boundary implementation requires minimal changes.
  - Add/adjust focused verification for boundary behavior and Submesh construction.
- Out of scope:
  - New mesh generators beyond what Firedrake already provides in this repo.
  - Performance optimization unrelated to correctness.
  - Visualization/post-processing redesign.

## Data Sources
- `acoustic_solver.py`: current solver structure, parameters, and weak form implementation (`view`, `rg`).
- `instruction_loopy.text`: requested behavior (extended domain + Submesh + Clayton A1).
- `test_submesh_*.py` (especially `test_submesh_solve.py`, `test_submesh_assign.py`, `test_submesh_basics.py`): reference Submesh/RelabeledMesh/interface-measure patterns (`view`, `rg`).
- Git history: `git log --oneline -20` and `git log --oneline -- acoustic_solver.py` for recent behavior expectations and potential regression context.
- Generated artifacts: `acoustic_solution/*.vtu` for immediate measurable output baseline (`glob`).

## Requirements
### Functional
- [F1] Partition a parent mesh into labeled physical and extended regions using Firedrake labeling (`DG0`/`RelabeledMesh`) and instantiate corresponding `Submesh` objects.
- [F2] Assemble forms so physical and extended solutions are coupled consistently across their interface using Submesh-compatible measures/intersections.
- [F3] Apply Clayton A1 absorbing boundary condition terms on selected outer boundary labels of the extended domain.
- [F4] Preserve existing interior wave equation update form and source forcing shape unless a boundary-term integration change is strictly required.
- [F5] Expose boundary-label selection explicitly (inputs or clearly defined constants) so behavior is deterministic and testable.
- [F6] Produce finite solution outputs for at least one full forward run with absorbing mode enabled.

### Non-Functional
- [N1] Performance: maintain current step loop viability (same order of timesteps and no catastrophic slowdown for current mesh size).
- [N2] Security/Privacy: no external data transfer; all computation remains local code/data.
- [N3] Accessibility: N/A for UI; maintain clear function naming/docstrings and deterministic CLI-testability.

## User Stories (MVP)
- As a Firedrake developer, I want to run the acoustic solver on physical+extended Submeshes so that absorbing boundaries can be modeled without changing interior physics.
- As a maintainer, I want a deterministic way to select Clayton boundary labels so that I can test reflective vs absorbing behavior reliably.
- As a researcher, I want output fields from an absorbing-boundary run to remain finite and stable over the configured simulation time.

## Success Metrics
- `acoustic_solver.py` contains Submesh-based physical/extended domain construction and no longer has zero Submesh references (target: `rg "Submesh" acoustic_solver.py` > 0).
- Clayton A1 boundary logic is present and selectable (target: boundary-condition code path exists and is exercised by tests).
- Forward-run smoke test passes with absorbing mode and returns finite norm(s) over the configured horizon.
- Regression check: existing relevant submesh tests used as references remain green for untouched behavior.

## Risks & Mitigations
- Incorrect region/interface labeling → Reuse proven `RelabeledMesh` + `Submesh` patterns from `test_submesh_solve.py` and assert label consistency.
- Boundary-term sign or facet selection errors → Add focused tests comparing absorbing vs reflective boundary outcomes.
- Drift from intended API/history → Use recent `git log` expectations as guidance and document any deliberate API deviations.

## Open Questions
- Which boundary labels are the canonical targets for Clayton A1 in this project’s intended mesh setup (all non-interface outer labels vs explicit subset)?
- Should absorbing-vs-reflective behavior be controlled via function arguments, config constants, or both?
- Is preserving legacy `solve_acoustic_submesh(...)` API compatibility required in addition to updating `main()` flow?

## Assumptions
- The requested change is a feature completion for the current working tree, where `acoustic_solver.py` currently lacks Submesh/Clayton implementation (directly evidenced by file contents and searches).
- Existing `test_submesh_*` files are the authoritative in-repo reference for Submesh semantics because no active `test_acoustic_solver.py` is present in the current tree.
- Measurable physics acceptance will be based on deterministic finite-run checks and relative absorbing-vs-reflective behavior, not external benchmark datasets (none found in repo). — Acceptance: outline scope and milestones

## Phase: implement
<!-- loopy:phase implement -->

- [ ] Implement: [needs refinement] ● List directory .
  └ 15 files found

● Read instruction_loopy.text
  └ 8 lines read

● Show recent commits
  $ git --no-pager log --oneline -20
  └ 21 lines...

● SQL: Create and start todos
  └ 3 row(s) inserted. Last inserted row ID: 3.

● Glob "**/*acoustic*" in /Users/ddolci/dev_code/submesh_examples
  └ 56 files found

● Grep "Submesh|clayton|Clayton|absorbing|extended
domain|A1|physical|interface_label|clayton_labels" (/Users/ddolci/dev_code/submesh_examples)
  └ 64 lines found

● Read acoustic_solver.py
  └ 89 lines read

● Read test_submesh_solve.py lines 400-560
  └ 161 lines read

● Glob "**/test*acoustic*.py" in /Users/ddolci/dev_code/submesh_examples
  └ No matches found

✗ Count VTU snapshots
  $ python - <<'PY'
  import glob
  print(len(glob.glob('acoustic_solution/acoustic_solution_*.vtu')))
  PY
  Permission denied and could not request permission from user

● Grep "Submesh" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Grep "Clayton|clayton|absorbing|A1" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Show acoustic_solver commit history
  $ git --no-pager log --oneline -- acoustic_solver.py | head -20
  └ 19 lines...

● Grep "dt\s*=|final_time\s*=|frequency_peak\s*=|total_steps\s*=|if step % 10 == 0"
(/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 5 lines found

● Check tracked acoustic files
  $ git --no-pager status --short && git --no-pager ls-files | rg
  'acoustic|submesh_acoustic|test_acoustic'
  └ 63 lines...

● Read test_submesh_solve.py lines 429-465
  └ 35 lines read

● Read test_submesh_assign.py lines 1-80
  └ 80 lines read

● Read test_submesh_basics.py
  └ 16 lines read

● Todo started: inspect-code

● Todo queried:

● Todo completed: write-prd

● Todo queried:

# PRD: Extended-Domain Acoustic Solver with Submesh and Clayton A1 ABC

## Problem Statement
`acoustic_solver.py` currently solves on a single domain without Submesh-based physical/extended partitioning or Clayton A1 absorbing boundaries, so it does not implement the requested extended-domain boundary treatment.

## Current Baseline
- Submesh usage in `acoustic_solver.py`: **0 matches** for `Submesh` (source: `rg` count on `acoustic_solver.py`).
- Clayton/absorbing boundary implementation in `acoustic_solver.py`: **0 matches** for `Clayton|clayton|absorbing|A1` (source: `rg` count on `acoustic_solver.py`).
- Current solver setup is single-domain: `UnitSquareMesh(80, 80)`, `dt=0.002`, `final_time=1.0`, `frequency_peak=7.0`, `total_steps=int(final_time/dt)+1`, output every 10 steps (source: `view`/`rg -n` on `acoustic_solver.py`).
- Existing output artifacts: **51 VTK snapshots** (`acoustic_solution_0.vtu` … `acoustic_solution_50.vtu`) indicating current run behavior (source: `glob` on `acoustic_solution/acoustic_solution_*.vtu`).

## Goals
- Add Submesh-based decomposition for physical and extended domains in `acoustic_solver.py`.
- Implement Clayton A1 absorbing boundary condition on the extended-domain outer boundary while preserving the core wave equation form.

## Non-Goals
- Rewriting the interior acoustic PDE discretization beyond boundary-condition-coupling needs.
- Building inversion/adjoint/optimization workflows.
- Refactoring unrelated submesh example tests.

## Users & Context
- Primary user: numerical PDE developer running Firedrake-based acoustic experiments from this repository.
- Secondary user(s): maintainers validating submesh coupling patterns against existing `test_submesh_*` references.
- Environment: internal Python/Firedrake research codebase, CLI/pytest workflow.

## Scope
- In scope:
  - Create physical vs extended region labeling and construct corresponding `Submesh` objects.
  - Add interface and outer-boundary terms needed for Clayton A1 behavior.
  - Keep current source injection/time-stepping workflow semantics unless boundary implementation requires minimal changes.
  - Add/adjust focused verification for boundary behavior and Submesh construction.
- Out of scope:
  - New mesh generators beyond what Firedrake already provides in this repo.
  - Performance optimization unrelated to correctness.
  - Visualization/post-processing redesign.

## Data Sources
- `acoustic_solver.py`: current solver structure, parameters, and weak form implementation (`view`, `rg`).
- `instruction_loopy.text`: requested behavior (extended domain + Submesh + Clayton A1).
- `test_submesh_*.py` (especially `test_submesh_solve.py`, `test_submesh_assign.py`, `test_submesh_basics.py`): reference Submesh/RelabeledMesh/interface-measure patterns (`view`, `rg`).
- Git history: `git log --oneline -20` and `git log --oneline -- acoustic_solver.py` for recent behavior expectations and potential regression context.
- Generated artifacts: `acoustic_solution/*.vtu` for immediate measurable output baseline (`glob`).

## Requirements
### Functional
- [F1] Partition a parent mesh into labeled physical and extended regions using Firedrake labeling (`DG0`/`RelabeledMesh`) and instantiate corresponding `Submesh` objects.
- [F2] Assemble forms so physical and extended solutions are coupled consistently across their interface using Submesh-compatible measures/intersections.
- [F3] Apply Clayton A1 absorbing boundary condition terms on selected outer boundary labels of the extended domain.
- [F4] Preserve existing interior wave equation update form and source forcing shape unless a boundary-term integration change is strictly required.
- [F5] Expose boundary-label selection explicitly (inputs or clearly defined constants) so behavior is deterministic and testable.
- [F6] Produce finite solution outputs for at least one full forward run with absorbing mode enabled.

### Non-Functional
- [N1] Performance: maintain current step loop viability (same order of timesteps and no catastrophic slowdown for current mesh size).
- [N2] Security/Privacy: no external data transfer; all computation remains local code/data.
- [N3] Accessibility: N/A for UI; maintain clear function naming/docstrings and deterministic CLI-testability.

## User Stories (MVP)
- As a Firedrake developer, I want to run the acoustic solver on physical+extended Submeshes so that absorbing boundaries can be modeled without changing interior physics.
- As a maintainer, I want a deterministic way to select Clayton boundary labels so that I can test reflective vs absorbing behavior reliably.
- As a researcher, I want output fields from an absorbing-boundary run to remain finite and stable over the configured simulation time.

## Success Metrics
- `acoustic_solver.py` contains Submesh-based physical/extended domain construction and no longer has zero Submesh references (target: `rg "Submesh" acoustic_solver.py` > 0).
- Clayton A1 boundary logic is present and selectable (target: boundary-condition code path exists and is exercised by tests).
- Forward-run smoke test passes with absorbing mode and returns finite norm(s) over the configured horizon.
- Regression check: existing relevant submesh tests used as references remain green for untouched behavior.

## Risks & Mitigations
- Incorrect region/interface labeling → Reuse proven `RelabeledMesh` + `Submesh` patterns from `test_submesh_solve.py` and assert label consistency.
- Boundary-term sign or facet selection errors → Add focused tests comparing absorbing vs reflective boundary outcomes.
- Drift from intended API/history → Use recent `git log` expectations as guidance and document any deliberate API deviations.

## Open Questions
- Which boundary labels are the canonical targets for Clayton A1 in this project’s intended mesh setup (all non-interface outer labels vs explicit subset)?
- Should absorbing-vs-reflective behavior be controlled via function arguments, config constants, or both?
- Is preserving legacy `solve_acoustic_submesh(...)` API compatibility required in addition to updating `main()` flow?

## Assumptions
- The requested change is a feature completion for the current working tree, where `acoustic_solver.py` currently lacks Submesh/Clayton implementation (directly evidenced by file contents and searches).
- Existing `test_submesh_*` files are the authoritative in-repo reference for Submesh semantics because no active `test_acoustic_solver.py` is present in the current tree.
- Measurable physics acceptance will be based on deterministic finite-run checks and relative absorbing-vs-reflective behavior, not external benchmark datasets (none found in repo). — Acceptance: behavior matches requirements

## Phase: verify
<!-- loopy:phase verify -->

- [ ] Verify: [needs refinement] Run tests (pytest test_acoustic_solver.py) — Acceptance: test suite passes
