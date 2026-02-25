# Loopy Plan Prompt

Timestamp: 2026-02-25T18:50:40.798Z

You are in PLANNING mode.
Goal: update the plan only. Do NOT implement anything. No code edits. No commits.

## Context
## Plan seed (PRD) (--generate-prd)
● SQL: Initialize todo tracking
  └ 0 row(s) inserted.

● List directory .
  └ 13 files found

✗ Create plan.md for task
  $ cat > /Users/ddolci/.copilot/session-state/8a45b56f-5345-44d1-ae9a-3fd9462231b4/plan.md
  <<'EOF'
  # Plan

  1. Research repository structure and solver/submesh-related evidence....
  Permission denied and could not request permission from user

● Grep "submesh|Clayton|full[_ -]?waveform|extended domain|acoustic|solver" in *.py
  └ 262 lines found

● Show recent commit history
  $ git --no-pager log --oneline -20
  └ 21 lines...

● Read acoustic_solver.py
  └ 284 lines read

● Read test_submesh_acoustic.py
  └ 70 lines read

● Grep "full[_ -]?waveform|inversion|FWI|adjoint" in *.py
  └ 1 file found

● Grep "^(from|import)\s+" in *.py
  └ 44 lines found

● Grep "Clayton|clayton" in *.py
  └ 2 files found

✗ Run non-parallel acoustic solver tests
  $ pytest -q test_submesh_acoustic.py -k 'not parallel'
  Permission denied and could not request permission from user

● Grep "misfit|objective|adjoint|gradient|minimize|ReducedFunctional|Control" (./acoustic_solver.py)
  └ No matches found

● Grep "^def test_" (./test_submesh_acoustic.py)
  └ 1 file found

● web_fetch: https://www.firedrakeproject.org/demos/full_waveform_inversion.py.html
  └ Contents of https://www.firedrakeproject.org/demos/full_waveform_inversion.py...

● Grep "clayton_labels|interface_label|boundary_labels" (./acoustic_solver.py)
  └ 1 file found

● Grep "^def\s+acoustic_solve|^def\s+solve_acoustic_submesh" (./acoustic_solver.py)
  └ 2 lines found

● Grep "Ensemble|ReducedFunctional|minimize|firedrake\.adjoint|ricker|VertexOnlyMesh|Cofunction" in
*.py
  └ 4 lines found

● Grep "^def test_" in test_*.py
  └ 9 files found

● Grep "clayton_labels" (./acoustic_solver.py)
  └ 1 file found

● Grep "interface_label" (./acoustic_solver.py)
  └ 1 file found

● Grep "Ensemble|ReducedFunctional|minimize|Control|wave_equation_solver|ricker_wavelet"
(./acoustic_solver.py)
  └ No matches found

● Grep "RectangleMesh\(8, 8, 1.0, 1.0, quadrilateral=True\)" in *.py
  └ 2 files found

● Grep "Submesh\(" (./acoustic_solver.py)
  └ 1 file found

● Glob "*.py"
  └ 10 files found

● Glob "test_*.py"
  └ 9 files found

● Glob "*.{toml,yaml,yml,ini,cfg,md,txt}"
  └ 1 file found

● Grep "Clayton A1|Clayton|clayton" (./acoustic_solver.py)
  └ 1 file found

● Grep "extended-domain|extended domain|extended_submesh" (./acoustic_solver.py)
  └ 1 file found

● Grep "full_waveform_inversion|full waveform inversion|FWI" in *.py
  └ No matches found

● Grep "clayton_labels|interface_label" (./test_submesh_acoustic.py)
  └ 1 file found

● Grep "receiver|observed|seismogram|misfit|gradient|optim|inversion|adjoint" (./acoustic_solver.py)
  └ No matches found

● Grep "source|wave_speed|dt|t_end|boundary_labels" (./acoustic_solver.py)
  └ 1 file found

● Todo started: research-codebase

● Todo queried:

● Todo started: draft-prd

● Todo queried:

# PRD: FWI-Style Submesh Acoustic Solver with Clayton BC

## Problem Statement
Implement a Firedrake solver workflow aligned with the Full-Waveform Inversion (FWI) demo while preserving this project’s submesh-based extended-domain Clayton absorbing boundary condition behavior.

## Current Baseline
- Codebase size: 10 Python files total, 9 test modules, 58 test functions (source: `glob "*.py"`, `glob "test_*.py"`, `rg "^def test_" --count`).
- Acoustic surface area: 1 solver module (`acoustic_solver.py`) with 2 solver entry points (`acoustic_solve`, `solve_acoustic_submesh`) and 4 acoustic tests (source: `view acoustic_solver.py`, `rg "^def test_" --count test_submesh_acoustic.py`).
- Existing boundary implementation: `Submesh(` appears 2 times and `clayton_labels` appears 5 times in `acoustic_solver.py` (source: `rg --count`).
- FWI orchestration is absent in current solver: 0 matches in `acoustic_solver.py` for `Ensemble|ReducedFunctional|minimize|Control|misfit|gradient|inversion` (source: `rg --count -i`).
- Recent change concentration exists around this area (source: `git log --oneline -20`; multiple recent commits explicitly reference `acoustic_solver.py` and `test_submesh_acoustic.py`).

## Goals
- Add an FWI-capable solver path following the Firedrake demo pattern (forward solve, misfit, gradient, optimization loop).
- Preserve extended-domain submesh construction and Clayton A1 absorbing treatment on outer non-interface boundaries.
- Maintain backward compatibility with existing acoustic API usage and diagnostics.

## Non-Goals
- Reworking unrelated submesh tests/modules outside acoustic/FWI scope.
- Adding 3D inversion support.
- Building production-scale inversion workflows or large-scale data pipelines.

## Users & Context
- Primary user: Firedrake developer/researcher prototyping seismic inversion with submesh coupling.
- Secondary user(s): CI maintainers validating acoustic/submesh regressions.
- Environment: Python/Firedrake (MPI-capable), script-driven local and CI execution.

## Scope
- In scope:
  - Extend solver capabilities to include FWI-style objective and optimization workflow.
  - Keep submesh split (extended + interior) and Clayton BC semantics on extended-domain boundaries.
  - Add/adjust acoustic tests to cover inversion workflow and boundary invariants.
- Out of scope:
  - GUI or visualization products.
  - External seismic data ingestion/ETL systems.
  - Redesign of finite-element discretizations unrelated to requested capability.

## Data Sources
- `acoustic_solver.py`: current forward solve API, submesh labeling, interface and Clayton handling (`view`, `rg`).
- `test_submesh_acoustic.py`: expected behavior for one-step solve and reflective-vs-Clayton comparison (`view`, `rg`).
- Git history: `git --no-pager log --oneline -20` for recent solver/test changes.
- Firedrake reference demo: `https://www.firedrakeproject.org/demos/full_waveform_inversion.py.html` (retrieved via `web_fetch`) for target FWI workflow structure.

## Requirements
### Functional
- [F1] Provide an FWI driver entry point that performs: forward modeling, receiver sampling, misfit accumulation, gradient evaluation, and iterative model update.
- [F2] Include source-time behavior consistent with the reference demo (Ricker wavelet) and support multiple sources/receivers.
- [F3] Preserve current extended-domain submesh construction and coupling structure; Clayton damping must apply only on non-interface extended-boundary labels.
- [F4] Preserve diagnostic outputs for interface/boundary behavior (`interface_label`, `clayton_labels`) and expose inversion diagnostics (objective history, iteration count).
- [F5] Keep `solve_acoustic_submesh(...)` callable with existing argument shape and return keys used by current tests.
- [F6] Add deterministic tests for: non-negative misfit, objective decrease over optimization, and retained Clayton-vs-reflective norm behavior.

### Non-Functional
- [N1] Performance: small benchmark inversion smoke run must complete within 300 seconds in CI-scale settings.
- [N2] Security/Privacy: no outbound data transfer; all observed/synthetic data handling remains local/in-memory unless explicitly file-configured.
- [N3] Accessibility: API remains script-first with explicit docstrings, typed parameters, and reproducible defaults.

## User Stories (MVP)
- As a Firedrake user, I want an end-to-end small FWI run so that I can validate inversion plumbing quickly.
- As an acoustic solver developer, I want Clayton BC preserved on the extended submesh so that absorbing-boundary behavior remains consistent.
- As a maintainer, I want regression tests for inversion objective trend and boundary-label semantics so that future changes are safe.

## Success Metrics
- Misfit reduction: for a fixed small benchmark, `J_final <= 0.8 * J_initial` within at most 20 optimization iterations.
- Boundary behavior consistency: reflective-vs-Clayton comparison continues to satisfy `solution_norm(clayton) <= solution_norm(reflective)` under equivalent setup.
- Compatibility: all 4 tests in `test_submesh_acoustic.py` pass with unchanged external call signatures.

## Risks & Mitigations
- MPI/runtime instability in tests → keep dedicated CI-scale inversion smoke configuration and avoid long horizon defaults.
- Adjoint integration complexity with submesh coupling → stage delivery (forward+misfit first, then gradient+optimizer) with checkpoints.
- Boundary marker regressions → add explicit assertions for interface-marker and Clayton-label partitioning.

## Open Questions
- Should MVP include ensemble source parallelism (`Ensemble`) immediately, or start with single-source-loop execution?
- What optimizer stop criteria are required for acceptance (`ftol`, max iterations, or absolute misfit threshold)?
- Is synthetic observed data sufficient for MVP, or is file-provided observed data required now?

## Assumptions
- Target remains 2D-only because current solver explicitly enforces `mesh.topological_dimension() == 2`.
- Current boundary semantics are authoritative: interface labels are inferred; Clayton damping applies to provided outer labels excluding interface labels.
- Demo-aligned implementation may use Firedrake adjoint optimization patterns (e.g., reduced functional + L-BFGS-B) to match requested source material.
- Runtime execution baselines (e.g., wall-clock test duration, pass/fail execution in this session) were unavailable due shell permission restrictions on non-git test commands, so baseline metrics are derived from static code and repository history.



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
test_command: pytest test_submesh_acoustic.py
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

## Phase: plan
<!-- loopy:phase plan -->

- [ ] Plan: [needs refinement] ● SQL: Initialize todo tracking
  └ 0 row(s) inserted.

● List directory .
  └ 13 files found

✗ Create plan.md for task
  $ cat > /Users/ddolci/.copilot/session-state/8a45b56f-5345-44d1-ae9a-3fd9462231b4/plan.md
  <<'EOF'
  # Plan

  1. Research repository structure and solver/submesh-related evidence....
  Permission denied and could not request permission from user

● Grep "submesh|Clayton|full[_ -]?waveform|extended domain|acoustic|solver" in *.py
  └ 262 lines found

● Show recent commit history
  $ git --no-pager log --oneline -20
  └ 21 lines...

● Read acoustic_solver.py
  └ 284 lines read

● Read test_submesh_acoustic.py
  └ 70 lines read

● Grep "full[_ -]?waveform|inversion|FWI|adjoint" in *.py
  └ 1 file found

● Grep "^(from|import)\s+" in *.py
  └ 44 lines found

● Grep "Clayton|clayton" in *.py
  └ 2 files found

✗ Run non-parallel acoustic solver tests
  $ pytest -q test_submesh_acoustic.py -k 'not parallel'
  Permission denied and could not request permission from user

● Grep "misfit|objective|adjoint|gradient|minimize|ReducedFunctional|Control" (./acoustic_solver.py)
  └ No matches found

● Grep "^def test_" (./test_submesh_acoustic.py)
  └ 1 file found

● web_fetch: https://www.firedrakeproject.org/demos/full_waveform_inversion.py.html
  └ Contents of https://www.firedrakeproject.org/demos/full_waveform_inversion.py...

● Grep "clayton_labels|interface_label|boundary_labels" (./acoustic_solver.py)
  └ 1 file found

● Grep "^def\s+acoustic_solve|^def\s+solve_acoustic_submesh" (./acoustic_solver.py)
  └ 2 lines found

● Grep "Ensemble|ReducedFunctional|minimize|firedrake\.adjoint|ricker|VertexOnlyMesh|Cofunction" in
*.py
  └ 4 lines found

● Grep "^def test_" in test_*.py
  └ 9 files found

● Grep "clayton_labels" (./acoustic_solver.py)
  └ 1 file found

● Grep "interface_label" (./acoustic_solver.py)
  └ 1 file found

● Grep "Ensemble|ReducedFunctional|minimize|Control|wave_equation_solver|ricker_wavelet"
(./acoustic_solver.py)
  └ No matches found

● Grep "RectangleMesh\(8, 8, 1.0, 1.0, quadrilateral=True\)" in *.py
  └ 2 files found

● Grep "Submesh\(" (./acoustic_solver.py)
  └ 1 file found

● Glob "*.py"
  └ 10 files found

● Glob "test_*.py"
  └ 9 files found

● Glob "*.{toml,yaml,yml,ini,cfg,md,txt}"
  └ 1 file found

● Grep "Clayton A1|Clayton|clayton" (./acoustic_solver.py)
  └ 1 file found

● Grep "extended-domain|extended domain|extended_submesh" (./acoustic_solver.py)
  └ 1 file found

● Grep "full_waveform_inversion|full waveform inversion|FWI" in *.py
  └ No matches found

● Grep "clayton_labels|interface_label" (./test_submesh_acoustic.py)
  └ 1 file found

● Grep "receiver|observed|seismogram|misfit|gradient|optim|inversion|adjoint" (./acoustic_solver.py)
  └ No matches found

● Grep "source|wave_speed|dt|t_end|boundary_labels" (./acoustic_solver.py)
  └ 1 file found

● Todo started: research-codebase

● Todo queried:

● Todo started: draft-prd

● Todo queried:

# PRD: FWI-Style Submesh Acoustic Solver with Clayton BC

## Problem Statement
Implement a Firedrake solver workflow aligned with the Full-Waveform Inversion (FWI) demo while preserving this project’s submesh-based extended-domain Clayton absorbing boundary condition behavior.

## Current Baseline
- Codebase size: 10 Python files total, 9 test modules, 58 test functions (source: `glob "*.py"`, `glob "test_*.py"`, `rg "^def test_" --count`).
- Acoustic surface area: 1 solver module (`acoustic_solver.py`) with 2 solver entry points (`acoustic_solve`, `solve_acoustic_submesh`) and 4 acoustic tests (source: `view acoustic_solver.py`, `rg "^def test_" --count test_submesh_acoustic.py`).
- Existing boundary implementation: `Submesh(` appears 2 times and `clayton_labels` appears 5 times in `acoustic_solver.py` (source: `rg --count`).
- FWI orchestration is absent in current solver: 0 matches in `acoustic_solver.py` for `Ensemble|ReducedFunctional|minimize|Control|misfit|gradient|inversion` (source: `rg --count -i`).
- Recent change concentration exists around this area (source: `git log --oneline -20`; multiple recent commits explicitly reference `acoustic_solver.py` and `test_submesh_acoustic.py`).

## Goals
- Add an FWI-capable solver path following the Firedrake demo pattern (forward solve, misfit, gradient, optimization loop).
- Preserve extended-domain submesh construction and Clayton A1 absorbing treatment on outer non-interface boundaries.
- Maintain backward compatibility with existing acoustic API usage and diagnostics.

## Non-Goals
- Reworking unrelated submesh tests/modules outside acoustic/FWI scope.
- Adding 3D inversion support.
- Building production-scale inversion workflows or large-scale data pipelines.

## Users & Context
- Primary user: Firedrake developer/researcher prototyping seismic inversion with submesh coupling.
- Secondary user(s): CI maintainers validating acoustic/submesh regressions.
- Environment: Python/Firedrake (MPI-capable), script-driven local and CI execution.

## Scope
- In scope:
  - Extend solver capabilities to include FWI-style objective and optimization workflow.
  - Keep submesh split (extended + interior) and Clayton BC semantics on extended-domain boundaries.
  - Add/adjust acoustic tests to cover inversion workflow and boundary invariants.
- Out of scope:
  - GUI or visualization products.
  - External seismic data ingestion/ETL systems.
  - Redesign of finite-element discretizations unrelated to requested capability.

## Data Sources
- `acoustic_solver.py`: current forward solve API, submesh labeling, interface and Clayton handling (`view`, `rg`).
- `test_submesh_acoustic.py`: expected behavior for one-step solve and reflective-vs-Clayton comparison (`view`, `rg`).
- Git history: `git --no-pager log --oneline -20` for recent solver/test changes.
- Firedrake reference demo: `https://www.firedrakeproject.org/demos/full_waveform_inversion.py.html` (retrieved via `web_fetch`) for target FWI workflow structure.

## Requirements
### Functional
- [F1] Provide an FWI driver entry point that performs: forward modeling, receiver sampling, misfit accumulation, gradient evaluation, and iterative model update.
- [F2] Include source-time behavior consistent with the reference demo (Ricker wavelet) and support multiple sources/receivers.
- [F3] Preserve current extended-domain submesh construction and coupling structure; Clayton damping must apply only on non-interface extended-boundary labels.
- [F4] Preserve diagnostic outputs for interface/boundary behavior (`interface_label`, `clayton_labels`) and expose inversion diagnostics (objective history, iteration count).
- [F5] Keep `solve_acoustic_submesh(...)` callable with existing argument shape and return keys used by current tests.
- [F6] Add deterministic tests for: non-negative misfit, objective decrease over optimization, and retained Clayton-vs-reflective norm behavior.

### Non-Functional
- [N1] Performance: small benchmark inversion smoke run must complete within 300 seconds in CI-scale settings.
- [N2] Security/Privacy: no outbound data transfer; all observed/synthetic data handling remains local/in-memory unless explicitly file-configured.
- [N3] Accessibility: API remains script-first with explicit docstrings, typed parameters, and reproducible defaults.

## User Stories (MVP)
- As a Firedrake user, I want an end-to-end small FWI run so that I can validate inversion plumbing quickly.
- As an acoustic solver developer, I want Clayton BC preserved on the extended submesh so that absorbing-boundary behavior remains consistent.
- As a maintainer, I want regression tests for inversion objective trend and boundary-label semantics so that future changes are safe.

## Success Metrics
- Misfit reduction: for a fixed small benchmark, `J_final <= 0.8 * J_initial` within at most 20 optimization iterations.
- Boundary behavior consistency: reflective-vs-Clayton comparison continues to satisfy `solution_norm(clayton) <= solution_norm(reflective)` under equivalent setup.
- Compatibility: all 4 tests in `test_submesh_acoustic.py` pass with unchanged external call signatures.

## Risks & Mitigations
- MPI/runtime instability in tests → keep dedicated CI-scale inversion smoke configuration and avoid long horizon defaults.
- Adjoint integration complexity with submesh coupling → stage delivery (forward+misfit first, then gradient+optimizer) with checkpoints.
- Boundary marker regressions → add explicit assertions for interface-marker and Clayton-label partitioning.

## Open Questions
- Should MVP include ensemble source parallelism (`Ensemble`) immediately, or start with single-source-loop execution?
- What optimizer stop criteria are required for acceptance (`ftol`, max iterations, or absolute misfit threshold)?
- Is synthetic observed data sufficient for MVP, or is file-provided observed data required now?

## Assumptions
- Target remains 2D-only because current solver explicitly enforces `mesh.topological_dimension() == 2`.
- Current boundary semantics are authoritative: interface labels are inferred; Clayton damping applies to provided outer labels excluding interface labels.
- Demo-aligned implementation may use Firedrake adjoint optimization patterns (e.g., reduced functional + L-BFGS-B) to match requested source material.
- Runtime execution baselines (e.g., wall-clock test duration, pass/fail execution in this session) were unavailable due shell permission restrictions on non-git test commands, so baseline metrics are derived from static code and repository history. — Acceptance: outline scope and milestones

## Guardrails
# Loopy Guardrails

## Signs

## Output Rules
- Plan only.
- No implementation steps.
- No commits.
- Keep tasks small and unambiguous.
