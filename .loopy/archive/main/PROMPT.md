# Loopy Build Prompt

You are in BUILDING mode. Complete exactly one task from the current plan.

## Current Task

- [ ] Confirm reflective-vs-Clayton norm ordering (`solution_norm((2, 3, 4)) <= solution_norm((5,))`) and existing API-focused acoustic tests remain green.


## Situation
Phase: verify | Iteration: 9 | Rotation: standard

# Loopy Progress

- Iteration: 8
- Current phase: verify
- Last status: success
- Last test: pass @ 2026-02-25 16:32:54
- Last error: n/a
- Last bytes: 31482
- Rotation pending: no
- Started at: 2026-02-25T19:06:00.970Z
- Updated at: 2026-02-25T19:32:55.097Z

## History
- 2026-02-25T19:06:00.970Z iteration 1 success (test: pass @ 2026-02-25 16:05:33) [files: __pycache__/acoustic_solver.cpython-314.pyc]
- 2026-02-25T19:08:57.988Z iteration 2 success (test: pass @ 2026-02-25 16:08:57)
- 2026-02-25T19:12:22.937Z iteration 3 success (test: pass @ 2026-02-25 16:12:22)
- 2026-02-25T19:18:58.731Z iteration 4 success (test: pass @ 2026-02-25 16:18:40) [files: __pycache__/acoustic_solver.cpython-314.pyc, acoustic_solver.py, acoustic_submesh_solution.pvd, acoustic_submesh_solution]
- 2026-02-25T19:22:57.987Z iteration 5 success (test: pass @ 2026-02-25 16:22:57) [files: __pycache__/acoustic_solver.cpython-314.pyc, acoustic_solver.py]
- 2026-02-25T19:27:47.149Z iteration 6 success (test: pass @ 2026-02-25 16:27:46) [files: __pycache__/test_submesh_acoustic.cpython-314-pytest-9.0.2.pyc, acoustic_submesh_solution/acoustic_submesh_solution_0.vtu, test_submesh_acoustic.py]
- 2026-02-25T19:29:33.837Z iteration 7 success (test: pass @ 2026-02-25 16:29:33)
- 2026-02-25T19:32:55.097Z iteration 8 success (test: pass @ 2026-02-25 16:32:54)

## Phase History
- 2026-02-25T19:12:22.937Z phase plan complete
- 2026-02-25T19:12:22.937Z phase advanced: plan -> implement
- 2026-02-25T19:27:47.149Z phase implement complete
- 2026-02-25T19:27:47.149Z phase advanced: implement -> verify



## Context
## Hints
## Findings from plan
1. **What was investigated**
   - Reviewed boundary-semantics requirements in `.loopy/PRD.md` and plan tasks in `.loopy/LOOPY_PLAN.md`, then cross-checked implemented partition logic in `acoustic_solver.py` and existing boundary assertions in `test_submesh_acoustic.py`.
2. **What was found (with evidence)**
   - `acoustic_solver.py` computes `interface_label` from submesh exterior markers absent from parent exterior markers and computes `clayton_labels` from user-provided labels intersected with outer non-interface markers.
   - Existing tests already cover reflective-only `(5,)` and Clayton `(2, 3, 4)` behavior plus norm ordering, but do not yet cover mixed unknown/interface label filtering or invalid-label input errors as a complete matrix.
3. **Conclusion**
   - Boundary semantics are stable and deterministic around a six-case matrix (BM-1..BM-6) that fully captures interface exclusion, Clayton inclusion, mixed-label filtering, and invalid-input failures.
4. **Recommended next action**
   - Implement the next-phase updates by adding forward-style objective wiring while preserving boundary partition logic and extending `test_submesh_acoustic.py` to execute BM-1..BM-6 exactly.

## Findings from implement
1. **What was investigated**
   - Expanded `test_submesh_acoustic.py` against the BM-1..BM-6 matrix in `.loopy/LOOPY_PLAN.md`, focusing on mixed-label filtering behavior and Clayton-vs-reflective norm ordering.
2. **What was found (with evidence)**
   - BM-1 now asserts `(1, 2, 3, 4)` yields `interface_label == (5,)`, `clayton_labels == (2, 3, 4)`, and finite one-step norm.
   - BM-2/BM-3 now explicitly assert interface diagnostics and preserve `solution_norm((2, 3, 4)) <= solution_norm((5,))`.
   - BM-4 was added with `(2, 5, 99)` and confirms filtering to `clayton_labels == (2,)`.
   - BM-5/BM-6 were added and assert deterministic failures/messages for `boundary_labels=()` and `boundary_labels="bad_string"`.
   - Validation evidence: `pytest test_submesh_acoustic.py` completed with `7 passed in 9.63s`.
3. **Conclusion**
   - The BM-1..BM-6 boundary-semantics matrix is now fully exercised in acoustic tests, including mixed-label exclusion and invalid-input guardrails, while preserving existing acoustic behavior.
4. **Recommended next action**
   - Proceed to verify-phase checks by validating the updated BM-1..BM-6 assertions and retaining reflective-vs-Clayton norm ordering under the existing test command.

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

## Phase: verify
<!-- loopy:phase verify -->

- [x] Run `pytest test_submesh_acoustic.py`.
- [x] Validate BM-1..BM-6 boundary assertions, including mixed-label filtering `(2, 5, 99) -> clayton_labels == (2,)` and invalid-input errors for `()` and `"bad_string"`.
- [ ] Confirm reflective-vs-Clayton norm ordering (`solution_norm((2, 3, 4)) <= solution_norm((5,))`) and existing API-focused acoustic tests remain green.

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
