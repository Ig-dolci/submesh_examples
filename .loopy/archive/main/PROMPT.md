# Loopy Build Prompt

You are in BUILDING mode. Complete exactly one task from the current plan.

## Current Task

- [ ] update: finalize solve_acoustic_submesh docstrings in acoustic_solver.py to state boundary-label semantics, one-step controls (`dt`, `t_end`), and returned diagnostics (`solution_norm`, `interface_label`, `clayton_labels`) — Acceptance: python -c "import inspect, acoustic_solver as m; d=inspect.getdoc(m.solve_acoustic_submesh) or \"\"; assert \"boundary\" in d.lower() and \"dt\" in d and \"solution_norm\" in d and \"interface_label\" in d and \"clayton_labels\" in d" exits 0.


## Situation
Phase: regress-submesh-suite | Iteration: 9 | Rotation: standard

# Loopy Progress

- Iteration: 8
- Current phase: regress-submesh-suite
- Last status: success
- Last test: pass @ 2026-02-24 23:49:02
- Last error: n/a
- Last bytes: 52995
- Rotation pending: no
- Started at: 2026-02-24T18:13:04.054Z
- Updated at: 2026-02-25T02:49:02.463Z

## History
- 2026-02-24T18:13:04.054Z iteration 1 success (test: pass @ 2026-02-24 15:13:03) [files: acoustic_solver.py]
- 2026-02-24T18:17:05.313Z iteration 2 success (test: pass @ 2026-02-24 15:17:05) [files: acoustic_solver.py]
- 2026-02-24T18:28:29.003Z iteration 3 success (test: pass @ 2026-02-24 15:28:28) [files: acoustic_solver.py]
- 2026-02-24T18:31:01.504Z iteration 4 success (test: pass @ 2026-02-24 15:31:01) [files: test_submesh_acoustic.py]
- 2026-02-24T18:39:16.672Z iteration 5 success (test: pass @ 2026-02-24 15:39:16) [files: test_submesh_acoustic.py]
- 2026-02-24T18:43:07.002Z iteration 6 success (test: pass @ 2026-02-24 15:43:06) [files: test_submesh_acoustic.py]
- 2026-02-24T23:36:25.259Z stopped by signal
- 2026-02-25T02:47:30.254Z iteration 7 failure (test: fail @ 2026-02-24 23:47:30)
- 2026-02-25T02:49:02.463Z iteration 8 success (test: pass @ 2026-02-24 23:49:02) [files: acoustic_solver.py]

## Phase History
- 2026-02-24T18:28:29.003Z phase implement-acoustic-solver complete
- 2026-02-24T18:28:29.003Z phase advanced: implement-acoustic-solver -> add-acoustic-tests
- 2026-02-24T18:43:07.002Z phase add-acoustic-tests complete
- 2026-02-24T18:43:07.002Z phase advanced: add-acoustic-tests -> regress-submesh-suite



## Context
## Hints
## Findings from implement-acoustic-solver

1. **What was investigated**
   - Weak-form coupling patterns in `test_submesh_solve.py` (`EquationBC` on interface labels) and `test_submesh_assemble.py` (`intersect_measures` on `dx/ds` cross-domain terms) were mapped into `solve_acoustic_submesh(...)`.

2. **What was found (evidence)**
   - A stable formulation was obtained by solving on two cell submeshes (extended + interior), coupling them on interface label `(5,)`, and applying Clayton A1-like damping on selected outer `ds` labels.
   - One-step smoke solve succeeded with finite norm and no PETSc/Firedrake error:
     - `solution_norm=7.317674617615585e-05`
     - `interface_label=(5,)`
     - `clayton_labels=(2, 3, 4)`

3. **Conclusion**
   - The root issue was label-map mismatch when coupling parent-mesh interior facets directly to submesh boundary facets; using paired submeshes with `EquationBC` on the shared interface resolves mapping conflicts and gives a finite one-step solution.

4. **Recommended next action**
   - Implement `test_submesh_acoustic.py` to lock in this behavior with deterministic API/manufactured, reflective-vs-Clayton, and MPI compatibility tests using the returned `solution_norm`, `interface_label`, and `clayton_labels` fields.

## Findings from add-acoustic-tests

1. **What was investigated**
   - MPI marker conventions in `test_submesh_solve.py` (`@pytest.mark.parallel(nprocs=...)`) and `test_submesh_comm.py` (`@pytest.mark.parallel([1, 3])`) were compared and applied to the acoustic one-step API path.

2. **What was found (evidence)**
   - Added `test_solve_acoustic_submesh_parallel_one_step_finite_norm` in `test_submesh_acoustic.py` with `@pytest.mark.parallel([1, 3])`, running `solve_acoustic_submesh(...)` for one step (`dt=0.01`, `t_end=0.01`).
   - The test asserts `result["num_steps"] == 1` and `math.isfinite(result["solution_norm"])`.
   - Validation command passed: `pytest -q test_submesh_acoustic.py -k parallel` → `4 passed in 9.75s`.

3. **Conclusion**
   - The one-step acoustic submesh API is compatible with the repository’s MPI-marked pytest execution style and returns a finite norm in parallel-marked runs.

4. **Recommended next action**
   - Execute regress-submesh-suite checks (`test_submesh_assemble.py`, `test_submesh_solve.py`, and full `test_submesh_acoustic.py`) and then finalize solver docstrings around boundary semantics and reported diagnostics.

## PRD References
- section: Problem Statement
- section: Current Baseline
- section: Goals
- section: Non-Goals
- section: Users & Context
- section: Scope

## Plan
---
agent_command: copilot --allow-all
test_command: pytest -q
max_iterations: 50
max_minutes: 240
backoff_ms: 5000
rotate_bytes: 150000
git:
  branch: main
  commit: true
  commit_message: 'loopy: {change_type} {task_summary}'
phase_defaults:
  stop_on: all_checked
  test_command: pytest -q
phases:
  - id: implement-acoustic-solver
    title: Build solver core
    stop_on: tests_pass
    test_command: pytest -q test_submesh_acoustic.py -k 'api or manufactured'
  - id: add-acoustic-tests
    title: Add deterministic tests
    stop_on: tests_pass
    test_command: pytest -q test_submesh_acoustic.py
  - id: regress-submesh-suite
    title: Verify existing tests
    stop_on: tests_pass
    test_command: pytest -q test_submesh_assemble.py test_submesh_solve.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

## Phase: regress-submesh-suite
<!-- loopy:phase regress-submesh-suite -->

- [!] verify: run regression tests for existing coupling examples in test_submesh_assemble.py and test_submesh_solve.py after introducing the MPI-marked acoustic compatibility test — BLOCKED: `pytest -q test_submesh_assemble.py test_submesh_solve.py` repeatedly hangs at `test_submesh_solve.py::test_submesh_solve_simple[None-4]` during MPI/PETSc finalize and never exits in this environment.
- [x] verify: run the full acoustic test module (including MPI-marked compatibility coverage) to confirm serial and parallel paths remain stable — Acceptance: pytest -q test_submesh_acoustic.py exits 0.
- [ ] update: finalize solve_acoustic_submesh docstrings in acoustic_solver.py to state boundary-label semantics, one-step controls (`dt`, `t_end`), and returned diagnostics (`solution_norm`, `interface_label`, `clayton_labels`) — Acceptance: python -c "import inspect, acoustic_solver as m; d=inspect.getdoc(m.solve_acoustic_submesh) or \"\"; assert \"boundary\" in d.lower() and \"dt\" in d and \"solution_norm\" in d and \"interface_label\" in d and \"clayton_labels\" in d" exits 0.

## Requirements


## Rules
- Do not assume functionality is missing; search first.
- No stubs or placeholder implementations.
- Use subagents to study PRD/code; use only one subagent for tests.
- Use `.loopy/PRD.md` and the listed `prd_refs` before requirement-level decisions.
- Keep changes focused and maintain repo state.
- Deliver outcomes, not scaffolding. Fixing the root cause or implementing the feature is always higher priority than building tools to measure, verify, or monitor the problem.
- Focus on one task at a time. Do not check multiple boxes in a single iteration.
- Mark a task checkbox as [x] when the implementation is done.
- If a task is impossible or should be skipped, mark it with [~] or [-] and explain the reason inline.
- If a task is blocked by external factors after 3+ consecutive failures, mark it as [!] with a reason: `[!] task — BLOCKED: reason`. Blocked tasks do not block phase advancement.
- Complete all unchecked tasks in the current phase before tests will be run.
- Execute tests in your workflow and include a valid ```loopy_test_report``` JSON block in your response. Required schema: `{ "status": "pass|fail|skipped", "command": "the test command run", "summary": "one-line result", "evidence": "relevant output excerpt" }`. All four fields are required strings. Do NOT use arrays, nested objects, or extra fields like `tests` or `phase`.
- If tests fail after all tasks are checked, fix the failures before the phase can advance. Do not move on with broken tests.
- If the same task has failed for 3+ consecutive iterations, reassess your approach: read the error output carefully, consider reverting recent changes, or switch to plan mode to re-scope the task.
- If the plan is wrong or stale, switch to plan mode and regenerate it.
- If acceptance criteria are subjective, add and run judge tests (see `loopy add-judge`).
- Record any new guardrails if you detect repetition or drift.
- If your work reveals validation steps, metrics checks, or verifications that cannot be performed now because they depend on future data (e.g., future CI runs, post-deploy observations, production traffic), append them to `.loopy/FOLLOW_UP.md` as checklist items. Do NOT create plan tasks for future-dependent work. The follow-up file is for humans to act on after the automated work completes.

## Phase Lifecycle
- Phases follow a two-gate lifecycle: Gate 1 = all tasks checked [x] (or skipped [~]/[-] or blocked [!]), Gate 2 = test report status is pass.
- The validation report gate is NOT evaluated until every task in the current phase is checked. Focus on completing tasks first.
- Never cycle back to a previous phase. Phases are sequential and one-directional.
- When completing the LAST unchecked task of the current phase, append a structured summary to `.loopy/hints.md` under `## Findings from [phase name]`. Include: (1) what was investigated, (2) what was found with specific data or evidence, (3) the conclusion -- root cause, key insight, or decision, and (4) the recommended next action.
- When completing the LAST task of a phase, review EVERY task in the NEXT phase of LOOPY_PLAN.md and rewrite it based on your findings:
  - If a task is irrelevant given what you found, REMOVE it and replace with a task that addresses the actual finding.
  - If a task is too vague given what you now know, REWRITE it with concrete details (file paths, function names, specific changes).
  - If your findings reveal the solution, the next phase must IMPLEMENT that solution -- not build more analysis or measurement tooling around it.
  Keep the same phase id and structure. Do NOT add or remove phases or rewrite tasks beyond the next phase.
- If your work reveals that the PRD's Problem Statement, Baseline, Goals, or Success Metrics are inaccurate or based on assumptions disproven by evidence, update `.loopy/PRD.md` to reflect reality. The PRD is a living document -- keeping it aligned with findings ensures the remaining plan stays on track.

## Guardrails
# Loopy Guardrails

## Signs
