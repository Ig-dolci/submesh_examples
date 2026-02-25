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
