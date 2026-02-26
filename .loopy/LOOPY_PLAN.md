---
agent_command: copilot --allow-all
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
  test_command: pytest -q
phases:
  - id: implement-forward-solver
    title: Implement forward solver
    stop_on: all_checked
    test_command: pytest -q
  - id: add-acoustic-regression-tests
    title: Add acoustic tests
    stop_on: tests_pass
    test_command: pytest -q test_acoustic_solver.py
  - id: repo-validation
    title: Validate integration
    stop_on: tests_pass
    test_command: pytest -q
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

## PRD: Forward Acoustic Submesh Solver with Clayton A1 ABC

## Problem Statement
Implement a Firedrake-based forward-only acoustic wave solver that uses Submesh for physical/extended domains and Clayton A1 absorbing boundaries, preserving the tutorial’s source-term definition and excluding inversion logic.

## Current Baseline
- Acoustic solver Python modules in repo: **0** files matching `**/*acoustic*.py` (source: `glob`).
- Existing acoustic artifacts: **8** VTU timesteps (`t=0..7`) referenced in `acoustic_solution.pvd` and present in `acoustic_solution/*.vtu` (source: `view` + `glob` + `ls ... | wc -l`).
- Submesh-focused test coverage: **8** test files and **54** `def test_...` functions (source: `glob` + `rg` count).
- Submesh API usage density: **57** `Submesh(...)` call sites in `test_*.py` (source: `rg` count).
- Current working-tree regression signal: **2** deleted acoustic files (`acoustic_solver.py`, `test_acoustic_solver.py`) (source: `git status --short`).
- Recent related history: prior commits reference acoustic solver API constraints and Clayton/interface behavior (e.g., `cd926a0`, `ba535f3`, `96b441c`, `9757c14`) (source: `git log --oneline -20`).

## Goals
- Deliver a forward-wave-only acoustic implementation aligned with the Firedrake FWI tutorial’s wave equation and source-term construction.
- Model physical vs extended domains via Firedrake `Submesh` with explicit interface/boundary labeling.
- Apply Clayton A1 absorbing boundary condition on designated outer boundaries.
- Provide deterministic, automated tests validating API shape, boundary-label handling, and forward solve behavior.

## Non-Goals
- No full-waveform inversion loop, objective minimization, gradient/adjoint, or optimization updates.
- No redesign of existing Submesh generic tests outside acoustic scope.
- No change to source-wavelet form from tutorial (except parameter wiring).

## Users & Context
- Primary user: Firedrake developer/research engineer implementing seismic forward modeling in this repo.
- Secondary user(s): CI/test maintainers validating Submesh-acoustic behavior.
- Environment: internal Python + Firedrake + pytest workflow (MPI-capable test context).

## Scope
- In scope:
  - Forward acoustic PDE time-stepping implementation.
  - Source term preserved from tutorial pattern (Ricker-driven forcing onto dual space / equivalent established representation).
  - Submesh construction for physical/extended regions and interface-aware boundary partitioning.
  - Clayton A1 ABC on selected outer labels.
  - Unit/integration tests for API contract and basic physical sanity checks.
- Out of scope:
  - Inversion objective, adjoint gradient, LBFGS or any optimizer.
  - New visualization pipelines beyond existing artifact style.
  - Broad refactors of non-acoustic Submesh examples.

## Data Sources
- `instruction_loopy.text`: explicit task constraints (forward only, Submesh domains, Clayton A1).
- `test_submesh_*.py`: established Submesh labeling/intersection/solver usage patterns.
- `git log --oneline -20`: recent behavioral/API intent and potential regression clues.
- `git status --short`: current deleted acoustic-file signal.
- Firedrake tutorial page (`full_waveform_inversion.py` HTML): forward acoustic equation, weak form, and source-term pattern.
- `acoustic_solution.pvd` + `acoustic_solution/*.vtu`: currently available output snapshot baseline.

## Requirements
### Functional
- [F1] Provide a callable forward solver API (module-level function) that computes pressure field evolution over time and returns stable, documented outputs (at minimum final field and/or per-step snapshots).
- [F2] Implement only the forward acoustic equation with zero initial displacement/velocity and no inversion control flow.
- [F3] Preserve tutorial-consistent source-term semantics (Ricker time function driving spatial source representation) and expose source parameters (`frequency_peak`, location, amplitude, `dt`, `final_time`).
- [F4] Build physical and extended domains using Firedrake `Submesh`; define/retain interface label semantics for coupling/boundary handling.
- [F5] Apply Clayton A1 absorbing boundary condition on configured outer boundary labels; exclude interface boundaries from absorbing treatment.
- [F6] Allow reflective fallback (no absorbing term) for comparison tests.
- [F7] Add/restore automated tests that validate:
  - API signature/return keys,
  - boundary-label filtering,
  - forward run executes and produces expected timestep count,
  - absorbing vs reflective behavior ordering metric (e.g., lower boundary-reflection energy with Clayton).

### Non-Functional
- [N1] Performance: default test configuration must complete within CI-friendly runtime (small mesh / reduced timesteps mode).
- [N2] Security/Privacy: no external network/data dependencies at runtime; inputs local and deterministic.
- [N3] Accessibility: N/A for UI; code/test readability via clear parameter names and concise docstrings.

## User Stories (MVP)
- As a Firedrake developer, I want a forward-only acoustic solver API so that I can run wave propagation without inversion machinery.
- As a numerical developer, I want Submesh-based physical/extended domains so that absorbing boundaries can be applied on outer regions while preserving interface semantics.
- As a test maintainer, I want deterministic tests for Clayton-vs-reflective behavior so that regressions are caught quickly.

## Success Metrics
- Solver availability: 1 forward acoustic module + 1 test module present and discoverable by pytest in repo.
- Correctness gate: 100% pass on acoustic-targeted tests in default CI mode.
- Physics regression gate: absorbing configuration yields strictly improved boundary-reflection metric versus reflective baseline in defined benchmark case.
- Output consistency: produced timestep artifact count equals `int(final_time/dt)+1` for test runs.

## Risks & Mitigations
- Boundary-label misclassification (interface vs outer) → Reuse proven Submesh label filtering patterns from existing solver tests and add explicit tests.
- Source-term drift from tutorial → Encode formula directly from tutorial reference and freeze with unit checks on sampled values.
- Runtime instability/CI slowness → Provide reduced-size fast-test parameter set and separate heavier validation path.

## Open Questions
- Which exact public API name/file should be canonical now (`acoustic_solver.py`/`solve_acoustic_submesh`) given current working-tree deletions?
- Should Clayton A1 be mandatory default or opt-in via boundary label list?
- What reflection metric threshold should be enforced for pass/fail across platforms?

## Assumptions
- Prior acoustic files were intentionally part of expected scope and should be restored/replaced, because recent commit history references them while working tree shows deletion.
- Devito extended-domain example is guidance for domain layout only (not a required numerical discretization match), because direct notebook fetch was unavailable in this environment.
- Existing Firedrake/pytest infrastructure in this repo is the authoritative convention for implementation/testing patterns.

## Phase: implement-forward-solver
<!-- loopy:phase implement-forward-solver -->

- [ ] add: create `acoustic_solver.py` with public `solve_acoustic_submesh(...)` forward-only API (no inversion/adjoint code paths) and documented return structure — Acceptance: `rg -n "^def solve_acoustic_submesh\(" acoustic_solver.py` returns exactly one match and `rg -n "adjoint|LBFGS|optimi" acoustic_solver.py` returns no matches.
- [ ] implement: add Submesh domain construction in `acoustic_solver.py` that separates physical vs extended meshes and identifies interface labels before boundary treatment — Acceptance: file contains explicit `Submesh(` usage and logic that excludes interface labels from outer-boundary absorbing sets.
- [ ] implement: add Clayton A1 absorbing boundary contribution in the forward weak form in `acoustic_solver.py`, gated by absorbing-boundary labels with reflective fallback — Acceptance: with empty absorbing label list the absorbing term path is disabled, and with non-empty labels it is enabled, verified by targeted tests.
- [ ] implement: preserve tutorial-style Ricker source forcing in `acoustic_solver.py` with exposed parameters (`frequency_peak`, source location, amplitude, `dt`, `final_time`) — Acceptance: source term is parameterized by those names and tests confirm time-varying values and frequency sensitivity.

## Phase: add-acoustic-regression-tests
<!-- loopy:phase add-acoustic-regression-tests -->

- [ ] add: create `test_acoustic_solver.py` API-contract test for `solve_acoustic_submesh` inputs and return keys/shape — Acceptance: `pytest -q test_acoustic_solver.py -k api` exits 0.
- [ ] add: implement timestep-count test in `test_acoustic_solver.py` asserting output snapshots equal `int(final_time/dt)+1` for a fast deterministic setup — Acceptance: `pytest -q test_acoustic_solver.py -k timestep` exits 0.
- [ ] add: implement Clayton-vs-reflective behavior test in `test_acoustic_solver.py` using a deterministic outer-boundary reflection-energy metric — Acceptance: `pytest -q test_acoustic_solver.py -k clayton` exits 0 and asserts absorbing metric is strictly lower than reflective.

## Phase: repo-validation
<!-- loopy:phase repo-validation -->

- [ ] verify: run `pytest -q test_acoustic_solver.py` and resolve only acoustic-related failures in `acoustic_solver.py` and `test_acoustic_solver.py` — Acceptance: command exits 0.
- [ ] verify: run full `pytest -q` to ensure existing `test_submesh_*.py` behavior is preserved after acoustic restoration — Acceptance: command exits 0.
