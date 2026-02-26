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
  test_command: pytest -q test_acoustic_solver.py
phases:
  - id: tighten-forward-solver
    title: Tighten forward solver
    stop_on: all_checked
    test_command: pytest -q test_acoustic_solver.py
  - id: align-acoustic-regressions
    title: Align acoustic regressions
    stop_on: tests_pass
    test_command: pytest -q test_acoustic_solver.py
  - id: verify-submesh-compatibility
    title: Verify submesh compatibility
    stop_on: tests_pass
    test_command: pytest -q test_submesh_solve.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

<!-- loopy:seed ● SQL: Create initial todos
  └ 3 row(s) inserted. Last inserted row ID: 3.

● Read instruction_loopy.text
  └ 12 lines read

● Glob "*.py" in /Users/ddolci/dev_code/submesh_examples
  └ 10 files found

● Show recent commit history
  $ git --no-pager log --oneline -20
  └ 21 lines...

● List directory .
  └ 16 files found

● Read acoustic_solver.py
  └ 194 lines read

● Read test_acoustic_solver.py
  └ 44 lines read

● Grep "wave|source|clayton|submesh|inversion|extended|absorbing|A1" in *.py
(/Users/ddolci/dev_code/submesh_examples)
  └ 5 lines found

● Todo started: analyze-seed

✗ Run acoustic solver tests for baseline
  $ pytest -q test_acoustic_solver.py
  Permission denied and could not request permission from user

● Todo queried:

✗ Collect static baseline metrics
  $ python -V && python - <<'PY'
  import re, pathlib
  p=pathlib.Path('/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py')
  s=p.read_text()
  print('lines', len(s.splitlines()))...
  Permission denied and could not request permission from user

● Todo started: inspect-codebase

● Read test_submesh_solve.py
  └ 1 line read

● Grep "solve_acoustic_submesh|_ricker_wavelet|EquationBC|clayton_labels|interface_label|Submesh" in
 *.py (/Users/ddolci/dev_code/submesh_examples)
  └ 92 lines found

● Todo completed: inspect-codebase

● Todo started: draft-prd

● Todo queried:

● Read test_submesh_solve.py lines 420-490
  └ 71 lines read

● Glob
"{README*,pyproject.toml,setup.py,setup.cfg,requirements*.txt,pytest.ini,tox.ini,*.yml,*.yaml}" in
/Users/ddolci/dev_code/submesh_examples
  └ 1 file found

● Create ~/.copilot/session-state/5669db9b-c6fd-47e4-8b30-08d8651b45a6/plan.md

● List directory acoustic_solution
  └ 8 files found

● Read acoustic_solution.pvd
  └ 13 lines read

● Grep "^def test_" (/Users/ddolci/dev_code/submesh_examples/test_acoustic_solver.py)
  └ 1 file found

● Grep "^def test_" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 9 files found

● Todo completed: draft-prd

● Todo queried:

# PRD: Forward Acoustic Wave Solver on Firedrake Submeshes

## Problem Statement
Define and stabilize a forward-only acoustic wave equation implementation (with tutorial-consistent source term), using Firedrake submeshes for physical vs extended domains and A1 Clayton absorbing boundaries, without adding inversion workflow scope.

## Current Baseline
- Acoustic solver entry point: 1 public function (`solve_acoustic_submesh`) in `acoustic_solver.py` (source: file inspection with `view`).
- Acoustic regression coverage: 3 tests in `test_acoustic_solver.py` (source: `rg "^def test_" test_acoustic_solver.py`).
- Repository test footprint: 57 tests across `test_*.py` (source: `rg "^def test_" --count` on `test_*.py`).
- Existing output snapshots: 8 VTU timesteps listed in `acoustic_solution.pvd` (`acoustic_solution_0.vtu` … `_7.vtu`) (source: `view` on `acoustic_solution/` and `.pvd`).
- Current boundary/interface expectation: interface marker `(5,)` is asserted for rectangular baseline mesh (source: `test_acoustic_solver.py` and `test_submesh_solve.py` line with auto interface label 5).
- Current solver constraints: 2D mesh only; positive `dt` and `wave_speed`; non-negative `t_end`; Clayton labels filtered to user-provided non-interface outer markers (source: `acoustic_solver.py`).

## Goals
- Implement/retain a forward-only acoustic wave solve aligned with the requested tutorial scope (wave equation + source term only).
- Use Firedrake submesh decomposition to represent physical and extended domains with explicit interface coupling.
- Apply A1 Clayton boundary treatment only on eligible external boundaries of the extended domain.
- Preserve deterministic diagnostics and compatibility with existing acoustic tests.

## Non-Goals
- Full-waveform inversion, objective/adjoint optimization, parameter updates, or gradient-based loops.
- New meshing pipelines or external geometry preprocessing.
- Generalizing beyond the current 2D solver path.

## Users & Context
- Primary user: numerical developer/researcher running Firedrake submesh examples locally.
- Secondary user(s): test/CI maintainer validating acoustic behavior against regression tests.
- Environment: internal Python/Firedrake scientific-computing workflow.

## Scope
- In scope:
  - Forward acoustic PDE assembly and time stepping.
  - Tutorial-style source wavelet injection.
  - Physical/extended domain split via `Submesh`.
  - Interface continuity condition via `EquationBC`.
  - A1 Clayton boundary contribution on selected labels.
  - Output diagnostics and VTK snapshots.
- Out of scope:
  - Inversion objective, misfit computation, adjoint equations.
  - 3D support.
  - UI/visualization tooling beyond existing VTK writes.

## Data Sources
- `instruction_loopy.text`: explicit problem seed and constraints.
- `acoustic_solver.py`: current solver logic, API, validations, PDE terms, source and boundary handling.
- `test_acoustic_solver.py`: expected acoustic API behavior and baseline assertions.
- `test_submesh_solve.py`: reference submesh/interface coupling pattern and interface-label behavior.
- `git log --oneline -20`: recent history showing acoustic/clayton/interface-focused changes.
- `acoustic_solution.pvd` + `acoustic_solution/*.vtu`: existing generated timesteps and output cadence.

## Requirements
### Functional
- [F1] Provide a forward solver function that solves only the wave equation with source forcing (no inversion workflow).
- [F2] Build two non-empty submeshes from a parent mesh to represent physical and extended regions.
- [F3] Couple submesh solutions across their interface using an equation-based boundary condition.
- [F4] Apply A1 Clayton absorbing terms only to user-selected outer boundary labels that are not the interface label(s).
- [F5] Inject a tutorial-style source term combining temporal wavelet sampling and spatial source shape.
- [F6] Return structured diagnostics including mesh objects, selected labels, step count, solution handle, and finite norm.
- [F7] Preserve current API compatibility expected by `test_acoustic_solver.py`.

### Non-Functional
- [N1] Performance: complexity must scale with `num_steps = ceil(t_end/dt)` and avoid unnecessary per-step allocations.
- [N2] Security/Privacy: no external network/data access; writes limited to local VTK artifacts.
- [N3] Accessibility: deterministic, machine-readable diagnostics for agent-based validation (stable keys/types).

## User Stories (MVP)
- As a Firedrake developer, I want a forward-only acoustic solver over submeshes so that I can study wave propagation with an extended absorbing domain.
- As a test maintainer, I want stable interface/clayton label semantics so that regression tests detect behavioral drift.
- As a researcher, I want tutorial-consistent source injection so that numerical behavior is comparable to reference examples.

## Success Metrics
- All 3 acoustic regression tests in `test_acoustic_solver.py` pass, including interface-label and reflective-vs-clayton norm ordering checks.
- Solver returns finite `solution_norm` for the baseline rectangular case used in tests.
- Interface label behavior remains consistent with the established rectangular baseline expectation `(5,)`.
- Generated output remains a valid timestep collection (currently 8 snapshots in existing artifact pattern).

## Risks & Mitigations
- Tutorial mismatch risk (source or PDE differs subtly) → lock formulas/terms to documented reference and codify with targeted regression assertions.
- Boundary-label ambiguity risk across meshes → keep explicit partition logic and test interface/clayton label filtering.
- Scope creep into inversion logic → enforce strict non-goal and keep only forward solve path in API and docs.

## Open Questions
- Which exact tutorial source expression (temporal and spatial components) is the normative reference if multiple variants exist in the cited materials?
- Should source forcing be applied strictly on the physical submesh, or configurable between physical/extended domains?
- Is VTK write cadence (currently every 10 steps) a required behavior or an implementation detail?

## Assumptions
- The intended deliverable is limited to forward modeling because `instruction_loopy.text` explicitly repeats “keep only the wave equation and source term.”
- A 2D-only implementation is acceptable because current solver and tests enforce topological dimension 2.
- Existing API shape should remain stable because recent commits and tests emphasize compatibility constraints around `solve_acoustic_submesh(...)`.
- Runtime wall-clock and numerical baseline values were not added as pass/fail criteria because available evidence in this task is static code/tests/history and artifact files, not executable Firedrake test runs in this environment. -->

## Phase: tighten-forward-solver
<!-- loopy:phase tighten-forward-solver -->

- [ ] implement: update `acoustic_solver.py::solve_acoustic_submesh` to keep a strict forward-only path (wave equation + source term) and remove any inversion-oriented branches/outputs if present — Acceptance: function body contains no objective/adjoint/gradient update logic and returns the existing diagnostics contract.
- [ ] update: enforce boundary-label selection in `acoustic_solver.py::solve_acoustic_submesh` so A1 Clayton terms are applied only to user-provided outer labels excluding `interface_label`/`interface_labels` — Acceptance: code explicitly filters interface labels from Clayton label list before boundary term assembly.
- [ ] update: keep interface coupling in `acoustic_solver.py` on submesh interface via `EquationBC` for both submesh unknowns — Acceptance: variational form includes `EquationBC`-based continuity constraint tied to the computed interface marker(s).
- [ ] verify: confirm tutorial-style source injection path in `acoustic_solver.py` uses temporal wavelet sampling (e.g., `_ricker_wavelet`) multiplied by spatial source shape inside the time loop — Acceptance: source term assembly shows temporal*spatial composition and is called every step.
- [ ] update: normalize diagnostics emitted by `solve_acoustic_submesh` to stable keys (`mesh`, submesh handles, interface/clayton labels, `num_steps`, solution handle, `solution_norm`) — Acceptance: returned mapping contains these keys with finite `solution_norm` computation.

## Phase: align-acoustic-regressions
<!-- loopy:phase align-acoustic-regressions -->

- [ ] update: refine `test_acoustic_solver.py` assertions to lock API/diagnostics compatibility for `solve_acoustic_submesh` (required keys/types and finite norm) — Acceptance: test file asserts all expected diagnostics keys and `math.isfinite(solution_norm)`.
- [ ] add: extend `test_acoustic_solver.py` with an explicit check that interface marker semantics remain `(5,)` for the rectangular baseline — Acceptance: test fails if interface labels differ from `(5,)`.
- [ ] add: strengthen `test_acoustic_solver.py` reflective-vs-clayton behavior assertion using two solver invocations with/without Clayton labels — Acceptance: test asserts norm ordering remains consistent with absorbing behavior expectation.
- [ ] verify: run `pytest -q test_acoustic_solver.py` after edits — Acceptance: command exits 0 with all acoustic tests passing.

## Phase: verify-submesh-compatibility
<!-- loopy:phase verify-submesh-compatibility -->

- [ ] verify: run `pytest -q test_submesh_solve.py` to ensure submesh/interface coupling behavior remains compatible with existing expectations — Acceptance: command exits 0.
- [ ] verify: run `pytest -q test_submesh_assign.py test_submesh_assemble.py test_submesh_facet.py` as targeted smoke checks for label and assembly stability — Acceptance: command exits 0.
