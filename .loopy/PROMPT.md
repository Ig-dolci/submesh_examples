# Loopy Build Prompt

You are in BUILDING mode. Complete exactly one task from the current plan.



## Situation
Phase: plan | Iteration: 5 | Rotation: standard

# Loopy Progress

- Iteration: 4
- Current phase: plan
- Last status: success
- Last test: skipped @ 2026-03-03 09:49:34
- Last error: n/a
- Last bytes: 22476
- Rotation pending: no
- Started at: 2026-03-03T12:47:13.246Z
- Updated at: 2026-03-03T12:50:40.904Z

## History
- 2026-03-03T12:47:13.246Z iteration 1 success (test: skipped @ 2026-03-03 09:47:04)
- 2026-03-03T12:48:12.678Z iteration 2 success (test: skipped @ 2026-03-03 09:47:50)
- 2026-03-03T12:49:02.868Z iteration 3 success (test: skipped @ 2026-03-03 09:48:55)
- 2026-03-03T12:50:40.904Z iteration 4 success (test: skipped @ 2026-03-03 09:49:34)



## Context
## Hints
## Findings from plan

### What was investigated
- Read `acoustic_solver_submesh.py` (210 lines): current solver structure, submesh creation, Clayton ABC wiring, HABC blending, time loop.
- Read `ruben_test.py` (90 lines): confirmed Firedrake supports multiple submeshes from same parent mesh with distinct markers (999, 998).
- Read `.loopy/PRD.md`: full requirements, goals, risks, success metrics.

### What was found
1. **Single left-side submesh**: `indicator_function = conditional(x < 0.1, 1, 0)` with marker 999 (line 122). This creates an absorbing strip on the LEFT boundary (x=0), but per PRD G2, the left boundary should NOT have ABC.
2. **`wave_equation_solver()` is monolithic**: It builds one mixed space `V = V0 * V1` and one Clayton term. To support N submeshes, this needs to either (a) extend to `V = V0 * V1 * V2 * ... * VN` or (b) solve each submesh Clayton problem independently and blend results.
3. **Approach (b) is simpler**: Each submesh can have its own independent Clayton solve (TrialFunction/TestFunction on its own V_sub), coupled to parent via Dirichlet BCs. This avoids a large monolithic mixed system. The current code already does most of this — just needs to be looped.
4. **Weight function orientation**: Current weight ramps from x=0 outward: `(transition_width - x_sub) / transition_width`. For right boundary, it should ramp from x=1 inward: `(x_sub - (1-δ)) / δ`. For bottom, from z=0 upward: `(δ - z_sub) / δ`.
5. **Reference domain**: With c_max ≈ 2.0 and final_time = 1.0, wave travels ~2.0 units. A [0,5]×[0,5] domain with source at (0.3,0.1) has min distance to boundary of ~0.1 (bottom). Need to shift source or use [-2,3]×[-2,3] to ensure sufficient clearance. Actually, at z=0.1 and c_max=2.0, the wave reaches z=0 in 0.05s — the reference domain must be larger or the source placed further from boundaries. Using [−2, 3] × [−2, 3] with source at (0.3, 0.1) gives ≥2.1 units clearance in all directions.
6. **Corner overlap**: Where right strip (x>0.9) and bottom strip (z<0.1) overlap (the [0.9,1]×[0,0.1] corner), both weights are nonzero. Clamping `min(w_right + w_bottom, 1.0)` handles this.

### Conclusion
The implementation requires: (1) replacing the single left submesh with right+bottom submeshes, (2) running independent Clayton solves per submesh, (3) blending with correctly oriented weight functions, and (4) adding a large-domain reference solver for verification. The `ruben_test.py` pattern confirms multi-submesh is already supported.

### Recommended next action
Implement the changes in order: submesh construction → per-submesh Clayton wiring → blending → reference solver → error computation.

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
test_command: python3 acoustic_solver_submesh.py
max_iterations: 50
max_minutes: 120
backoff_ms: 5000
rotate_bytes: 150000
git:
  branch: habcs
  commit: true
  commit_message: 'loopy: {change_type} {task_summary}'
phase_defaults:
  stop_on: all_checked
  test_command: python3 acoustic_solver_submesh.py
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
    test_command: python3 acoustic_solver_submesh.py
prd_refs_defaults:
  - section: Problem Statement
  - section: Current Baseline
  - section: Goals
  - section: Non-Goals
  - section: Users & Context
  - section: Scope
---

# Plan

## Phase: plan
<!-- loopy:phase plan -->
- [x] Plan scope, goals, and constraints documented.

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
