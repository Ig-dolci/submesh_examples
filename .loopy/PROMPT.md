# Loopy Plan Prompt

Timestamp: 2026-02-26T12:56:57.789Z

You are in PLANNING mode.
Goal: update the plan only. Do NOT implement anything. No code edits. No commits.

## Context
## Plan seed (PRD) (--generate-prd)
● Read instruction_loopy.text
  └ 15 lines read

✗ Create session plan file
  $ cat > /Users/ddolci/.copilot/session-state/6cce8cb8-a8d6-4afe-9b94-0e4f7800cff4/plan.md
  <<'EOF'
  # Plan
  1. Read source seed and repository structure.
  2. Inspect relevant code/tests and recent git history....
  Permission denied and could not request permission from user

● Show recent git history
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager log --oneline -20
  └ 21 lines...

● List directory .
  └ 14 files found

● Glob "**/*.py" in /Users/ddolci/dev_code/submesh_examples
  └ 8 files found

● Grep "solve_acoustic_submesh|Clayton|absorbing|Submesh|forward wave|source term|acoustic"
(/Users/ddolci/dev_code/submesh_examples)
  └ 74 lines found

✗ List tracked files
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager ls-files | wc -l && git --no-pager
  ls-files | sed -n '1,120p'
  Permission denied and could not request permission from user

● Glob "**/*acoustic*.py" in /Users/ddolci/dev_code/submesh_examples
  └ No matches found

● Glob "**/*.{md,txt,rst,yml,yaml,toml,ini,cfg,pyproject}" in
/Users/ddolci/dev_code/submesh_examples
  └ 1 file found

● Grep "^def test_" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 8 files found

● Show git status short
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager status --short
  └ 10 lines...

● Read test_submesh_solve.py lines 1-260
  └ 260 lines read

● Read test_submesh_solve.py lines 430-560
  └ 131 lines read

● Read .pytest_cache/README.md
  └ 8 lines read

● Read acoustic_solution.pvd
  └ 13 lines read

● Count VTU snapshots
  $ cd /Users/ddolci/dev_code/submesh_examples && ls acoustic_solution/*.vtu | wc -l
  └ 2 lines...

✗ Show deleted solver from HEAD
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager show HEAD:acoustic_solver.py | sed
  -n '1,220p'
  Permission denied and could not request permission from user

✗ Show deleted acoustic test from HEAD
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager show HEAD:test_acoustic_solver.py |
   sed -n '1,260p'
  Permission denied and could not request permission from user

● SQL: Initialize task todos
  └ 2 row(s) inserted. Last inserted row ID: 2.

● Inspect latest commit files
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager show --name-only --oneline -1
  └ 8 lines...

● Count Submesh usages
  $ cd /Users/ddolci/dev_code/submesh_examples && rg -n "Submesh\(" test_*.py | wc -l && rg -n
  "@pytest.mark.parallel" test_*.py | wc -l
  └ 5 lines...

● Summarize test file/test counts
  $ cd /Users/ddolci/dev_code/submesh_examples && ls test_*.py | wc -l && rg "^def test_" test_*.py
  | wc -l
  └ 4 lines...

● Grep "Submesh\(" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 8 files found

● Grep "@pytest\.mark\.parallel" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 7 files found

● Grep "from firedrake import \*" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 8 files found

● Glob "acoustic_solution/*.vtu" in /Users/ddolci/dev_code/submesh_examples
  └ 8 files found

✗ History of acoustic solver path
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager log --oneline -- acoustic_solver.py
   test_acoustic_solver.py | sed -n '1,20p'
  Permission denied and could not request permission from user

✗ List acoustic artifacts sizes
  $ cd /Users/ddolci/dev_code/submesh_examples && ls -lh acoustic_solution.pvd
  acoustic_solution/*.vtu | sed -n '1,20p'
  Permission denied and could not request permission from user

● Todo started: research-context

● Todo queried:

✗ web_fetch:
https://raw.githubusercontent.com/devitocodes/devito/main/examples/seismic/abc_methods/04_habc.ipynb
  Permission denied and could not request permission from user

● web_fetch: https://www.firedrakeproject.org/demos/full_waveform_inversion.py.html
  └ Contents of https://www.firedrakeproject.org/demos/full_waveform_inversion.py...

● Get git status short
  $ cd /Users/ddolci/dev_code/submesh_examples && git --no-pager status --short
  └ 10 lines...

● Todo completed: draft-prd

● Todo queried:

# PRD: Forward Acoustic Submesh Solver with Clayton A1 ABC

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



## PRD References
- section: Problem Statement
- section: Current Baseline
- section: Goals
- section: Non-Goals
- section: Users & Context
- section: Scope

## Requirements
Study these sources before planning:
- `.loopy/PRD.md` (requirements)
- The project codebase (explore to understand structure and relevant files)
Use subagents for study and investigation; use only one subagent for tests.

## Plan
Compare specs against code. Produce a prioritized plan that closes gaps.
When the root cause of a problem is unclear, plan investigation tasks before implementation tasks.
Investigation tasks gather evidence (measurements, comparisons, API queries, log analysis) that informs what to fix.
Do not propose implementation changes to fix a problem you have not diagnosed -- plan the diagnosis first.
However, if the root cause IS clear from the codebase (e.g., a recent commit introduced a regression, a config is misconfigured, a dependency upgrade broke behavior), skip investigation and plan the fix directly.
If the existing plan is wrong or stale, replace it.
Keep tasks atomic, testable, and outcome-focused.
Tasks must be specific: include file paths, function names, or config keys when the target is known or discoverable.
Remove or rephrase tasks that a code agent cannot complete in a single session (long-running monitoring, manual approvals, multi-week tracking).
Every task must be verifiable with data available RIGHT NOW. Never plan tasks that depend on future events (e.g., 'wait for N future CI runs', 'measure post-deploy metrics over 2 weeks', 'compare before/after using future data'). If post-change validation needs future data, add it to `.loopy/FOLLOW_UP.md` instead of creating a plan task. The follow-up file is a human-reviewed checklist that survives archiving.
Do not assume anything is missing; search first.
If acceptance criteria are subjective, add judge tests (see `loopy add-judge`).
- Use explicit `prd_refs` in tasks/phases when requirements are not obvious from the task text.
- Phases use a two-gate completion model: Gate 1 = all tasks checked, Gate 2 = validation report passes.
- If a task is impossible to complete, mark it as skipped with [~] or [-] and include the reason in the task text.
- If a task is blocked by external factors after 3+ consecutive failures, mark it as [!] with a BLOCKED reason (e.g., `[!] task description — BLOCKED: reason`). Blocked tasks are excluded from phase gates.

## Current Plan
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

## Phase: implement-forward-solver
<!-- loopy:phase implement-forward-solver -->

- [ ] add: create `acoustic_solver.py` with public `solve_acoustic_submesh(...)` forward-only API (no inversion/adjoint code paths) and documented return structure — Acceptance: `rg -n "^def solve_acoustic_submesh\(" acoustic_solver.py` returns exactly one match and `rg -n "adjoint|LBFGS|optimi" acoustic_solver.py` returns no matches.
- [ ] implement: add Submesh domain construction in `acoustic_solver.py` that separates physical vs extended meshes and identifies interface labels before boundary treatment — Acceptance: file contains explicit `Submesh(` usage and logic that excludes interface labels from outer-boundary absorbing sets.
- [ ] implement: add Clayton A1 absorbing boundary contribution in the forward weak form in `acoustic_solver.py`, gated by absorbing-boundary labels with reflective fallback — Acceptance: with empty absorbing label list the absorbing term path is disabled, and with non-empty labels it is enabled, verified by targeted tests.
- [ ] implement: preserve tutorial-style Ricker source forcing in `acoustic_solver.py` with exposed parameters (`frequency_peak`, source location, amplitude, `dt`, `final_time`) — Acceptance: source term is parameterized by those names and tests confirm time-varying values and frequency sensitivity.

## Guardrails
# Loopy Guardrails

## Signs

## Output Rules
- Plan only.
- No implementation steps.
- No commits.
- Keep tasks small and unambiguous.
