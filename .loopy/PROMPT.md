# Loopy Build Prompt

You are in BUILDING mode. Complete exactly one task from the current plan.

## Current Task

- [ ] Plan: [needs refinement] ● Todo started: analyze-repo-context


## Situation
Phase: plan | Iteration: 1 | Rotation: standard

(no progress recorded yet)



## Context


## PRD References
- section: Problem Statement
- section: Current Baseline
- section: Goals
- section: Non-Goals
- section: Users & Context
- section: Scope

## Plan
---
agent_command: copilot
test_command: python3 acoustic_solver.py
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
  test_command: python3 acoustic_solver.py
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
    test_command: python3 acoustic_solver.py
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

- [ ] Plan: [needs refinement] ● Todo started: analyze-repo-context

● List directory .
  └ 13 files found

● Read test_submesh_acoustic.py
  └ 53 lines read

● Read acoustic_solver.py
  └ 234 lines read

● Glob "**/*.py" in /Users/ddolci/dev_code/submesh_examples
  └ 10 files found

● Grep "acoustic|RectangleMesh|RetangleMesh|UnitSquare|UnitCube|BoxMesh|acoustic_solve" in *.py
(/Users/ddolci/dev_code/submesh_examples)
  └ 52 lines found

● Show recent commit history
  $ git --no-pager log --oneline -20
  └ 14 lines...

✗ Compute acoustic_solver baseline code metrics
  $ python - <<'PY'
  import ast, pathlib
  p = pathlib.Path('/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py')
  src = p.read_text()
  mod = ast.parse(src)...
  Permission denied and could not request permission from user

● Grep "from firedrake import \*" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Grep "solve_acoustic_submesh\(" in *.py (/Users/ddolci/dev_code/submesh_examples)
  └ 2 files found

● Glob ".*" in /Users/ddolci/dev_code/submesh_examples
  └ 1 file found

● Grep "RectangleMesh\(" in *.py (/Users/ddolci/dev_code/submesh_examples)
  └ 62 lines found

● Grep """"" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Grep "^def\s+" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Grep "UnitIntervalMesh|UnitSquareMesh|RectangleMesh"
(/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Grep "UnitSquareMesh" (/Users/ddolci/dev_code/submesh_examples/test_submesh_acoustic.py)
  └ 1 file found

● Grep "RectangleMesh" (/Users/ddolci/dev_code/submesh_examples/test_submesh_acoustic.py)
  └ No matches found

● Read test_submesh_solve.py lines 1-120
  └ 120 lines read

● Read test_submesh_assemble.py lines 1-80
  └ 79 lines read

● Read test_submesh_assign.py lines 1-80
  └ 80 lines read

● Grep "UnitIntervalMesh" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Grep "RectangleMesh" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ No matches found

● Grep "@pytest\.mark\.parallel" (/Users/ddolci/dev_code/submesh_examples/test_submesh_acoustic.py)
  └ 1 file found

● Grep "^def test_" (/Users/ddolci/dev_code/submesh_examples/test_submesh_acoustic.py)
  └ 1 file found

● Show acoustic_solver commit history
  $ git --no-pager log --oneline -20 -- acoustic_solver.py
  └ 7 lines...

● Todo started: analyze-repo-context

● Grep "RectangleMesh" in *.py (/Users/ddolci/dev_code/submesh_examples)
  └ 6 files found

● Todo queried:

● Glob "plan.md" in /Users/ddolci/.copilot/session-state/246a4d96-bfe6-4b16-966c-447d7b9ea6c4
  └ No matches found

✗ Create session plan file
  $ cat > /Users/ddolci/.copilot/session-state/246a4d96-bfe6-4b16-966c-447d7b9ea6c4/plan.md
  <<'EOF'
  # Plan
  1. Gather evidence from acoustic_solver.py, related tests, and git history.
  2. Quantify current baseline metrics relevant to 2D RectangleMesh migration and code quality....
  Permission denied and could not request permission from user

● Grep "solve\(" (/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Grep "from firedrake import UnitSquareMesh|from firedrake import \*" in *.py
(/Users/ddolci/dev_code/submesh_examples)
  └ 10 files found

● Count lines in key files
  $ wc -l acoustic_solver.py test_submesh_acoustic.py
  └ 4 lines...

● Grep "__all__\s*=\s*\["solve_acoustic_submesh"\]"
(/Users/ddolci/dev_code/submesh_examples/acoustic_solver.py)
  └ 1 file found

● Check working tree status
  $ git --no-pager status --short
  └ 13 lines...

● Todo started: collect-evidence-baselines

✗ Run acoustic solver tests for baseline
  $ pytest -q test_submesh_acoustic.py
  Permission denied and could not request permission from user

✗ Check Python runtime availability
  $ python --version
  Permission denied and could not request permission from user

✗ Check pytest availability
  $ pytest --version
  Permission denied and could not request permission from user

● Todo completed: draft-agent-prd

● Read acoustic_solver.py lines 108-140
  └ 32 lines read

● Todo queried:

● Grep "^def\s+" (/Users/ddolci/dev_code/submesh_examples/test_submesh_acoustic.py)
  └ 1 file found

# PRD: 2D RectangleMesh Acoustic Solver Refactor

## Problem Statement
Rewrite the acoustic solve path into a clearly documented, Python-best-practice 2D implementation based on Firedrake `RectangleMesh`, while preserving current coupling behavior and diagnostics.

## Current Baseline
- Acoustic solver file size: **234 LOC** in `acoustic_solver.py` (source: `wc -l acoustic_solver.py`).
- `RectangleMesh` usage in acoustic path: **0 matches** in `acoustic_solver.py` and **0 matches** in `test_submesh_acoustic.py` (source: `rg "RectangleMesh"` on both files).
- Acoustic tests currently use `UnitSquareMesh`: **5 matches** in `test_submesh_acoustic.py` (source: `rg "UnitSquareMesh" test_submesh_acoustic.py`).
- Non-2D demo remains in solver: `UnitIntervalMesh` appears **1 time** in `acoustic_solver.py` (source: `rg "UnitIntervalMesh" acoustic_solver.py`).
- Python style gap in solver: wildcard import `from firedrake import *` appears **1 time** (source: `rg "from firedrake import \\*" acoustic_solver.py`).
- Acoustic test coverage inventory: **3 tests total**, **1 parallel-marked** (source: `rg "^def test_"` and `rg "@pytest\\.mark\\.parallel"` on `test_submesh_acoustic.py`).
- Local runtime execution status: Python/pytest commands currently return **Permission denied** in this environment (source: attempted `python --version`, `pytest -q test_submesh_acoustic.py`).

## Goals
- Deliver a 2D-first acoustic solver flow using `RectangleMesh` conventions already used across this repository.
- Improve code quality in `acoustic_solver.py` (explicit imports, clearer API, helper documentation, maintainable structure).
- Preserve existing acoustic solve outputs (`solution_norm`, `interface_label`, `clayton_labels`, `num_steps`) and expected behavior.

## Non-Goals
- Reworking unrelated 3D submesh tests/solvers in `test_submesh_solve.py`, `test_submesh_base.py`, etc.
- Redesigning the underlying acoustic physics model beyond what is needed for 2D `RectangleMesh` adaptation.
- Broad test-suite stabilization for known unrelated MPI finalize hangs.

## Users & Context
- Primary user: Firedrake developer/maintainer extending submesh examples and acoustic coupling tests.
- Secondary user(s): CI maintainers and contributors validating regression behavior.
- Environment: Internal Python/Firedrake test codebase (CLI + pytest workflow).

## Scope
- In scope:
  - Refactor `acoustic_solver.py` for explicit 2D `RectangleMesh` compatibility.
  - Update acoustic tests (`test_submesh_acoustic.py`) to use/validate `RectangleMesh`-based workflows.
  - Improve documentation and Python hygiene in the acoustic solver module.
- Out of scope:
  - Refactoring all legacy test modules that use wildcard imports.
  - Introducing new mesh types or a generalized multi-dimension API redesign.
  - Performance benchmarking infrastructure outside existing test/CI mechanisms.

## Data Sources
- `acoustic_solver.py`: current solver API, imports, docs, and mesh usage patterns (`view`, `rg`, `wc`).
- `test_submesh_acoustic.py`: current acoustic regression tests and mesh assumptions (`view`, `rg`).
- `test_submesh_assemble.py`, `test_submesh_solve.py`, `test_submesh_assign.py`: established `RectangleMesh` and `Submesh` patterns (`view`, `rg`).
- Git history: recent acoustic-related commits and intent (`git --no-pager log --oneline -20`, `git --no-pager log --oneline -20 -- acoustic_solver.py`).
- Runtime commands available for evidence: `rg`, `glob`, `view`, `git`; Python/pytest runtime checks currently blocked by permission policy.

## Requirements
### Functional
- [F1] Provide a 2D acoustic solve entry point aligned to the seed intent (`acoustic_solve`), while preserving compatibility with existing `solve_acoustic_submesh` call sites (alias or wrapper accepted).
- [F2] Ensure solver/test setup uses Firedrake `RectangleMesh(nx, ny, Lx, Ly, quadrilateral=True)` for 2D domain construction in the acoustic flow.
- [F3] Enforce 2D mesh validation (`topological_dimension == 2`) with explicit error messages for invalid mesh dimensionality.
- [F4] Preserve current result contract: returned diagnostics must include `solution_norm`, `interface_label`, `clayton_labels`, and `num_steps`.
- [F5] Keep current coupling semantics (extended/interior submesh construction and interface coupling) unless a change is required for 2D correctness and is covered by tests.
- [F6] Update/add acoustic tests to validate one-step finite norm, Clayton damping comparison, and parallel-marked path using 2D-compatible mesh setup.

### Non-Functional
- [N1] Performance: keep one linear solve per timestep in the acoustic loop (no additional timestep-level solves introduced).
- [N2] Security/Privacy: no external data transfer; all changes remain local code/test behavior.
- [N3] Accessibility: docstrings and naming must make API behavior, boundary-label semantics, and parameter expectations understandable without inspecting implementation internals.

## User Stories (MVP)
- As a Firedrake contributor, I want the acoustic solver to run as a clear 2D `RectangleMesh` workflow so that I can extend and debug it consistently with other 2D submesh examples.
- As a maintainer, I want documented, explicit-import acoustic solver code so that static review and future refactors are safer and faster.
- As a CI reviewer, I want acoustic tests to enforce 2D mesh expectations and preserved diagnostics so that regressions are detected quickly.

## Success Metrics
- `acoustic_solver.py` contains **>=1 `RectangleMesh`-based 2D path reference** and removes `UnitIntervalMesh` demo dependency for the primary acoustic flow (static grep checks).
- `acoustic_solver.py` wildcard imports reduced from **1 to 0** (`rg "from firedrake import \\*" acoustic_solver.py`).
- Acoustic test mesh usage shifts from **0 to >=1 `RectangleMesh` references** in `test_submesh_acoustic.py`.
- Acoustic regression suite (`test_submesh_acoustic.py`) passes in the **first CI run after merge**.
- Helper documentation coverage in `acoustic_solver.py` improves from current sparse helper docs to documented helper intent for all non-trivial helper functions.

## Risks & Mitigations
- Mesh/boundary marker behavior may differ when moving from `UnitSquareMesh` assumptions to `RectangleMesh` setup → Mitigate with explicit marker assertions in acoustic tests.
- API rename ambiguity (`acoustic_solve` vs `solve_acoustic_submesh`) may break callers → Mitigate with backward-compatible alias and deprecation note in docstring.
- Local runtime test execution is blocked in this environment → Mitigate by relying on static checks locally and gating merge on CI runtime validation.

## Open Questions
- Should `acoustic_solve` become the canonical public API name, or remain an alias to `solve_acoustic_submesh`?
- Should writing `acoustic_submesh_solution.pvd` remain default behavior or be made opt-in for cleaner test execution?
- What default `(nx, ny, Lx, Ly)` should the 2D `RectangleMesh` examples use for stable CI runtime?

## Assumptions
- “RetangleMesh” in the seed means Firedrake `RectangleMesh` (spelling correction inferred from repository usage).
- The change should focus on the acoustic module and its dedicated tests, not full-suite refactors.
- Runtime pass/fail baselines requiring Python execution cannot be collected locally due current permission restrictions; CI is available for final runtime verification. — Acceptance: outline scope and milestones

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
