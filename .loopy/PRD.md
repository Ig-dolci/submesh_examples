# PRD: Submesh Acoustic Wave Solver with Clayton A1 Hybrid Boundary Condition

## Problem Statement
The repository currently has only Firedrake submesh test examples and no acoustic-wave implementation, so we need a concrete solver that uses a submesh-based extended domain and Clayton A1 hybrid boundary conditions as specified in the referenced paper.

## Current Baseline
- Python implementation modules for this feature: **0** non-test modules (source: `glob "**/*.py"` and `glob "test_*.py"` both return only test files).
- Acoustic/Clayton feature footprint: **0 matches** for `acoustic|Clayton|A1|hibrid|hybrid` in repo files (source: `rg -i` across repository).
- Existing submesh construction patterns: **54 `Submesh(` constructor calls** across test files (source: `rg "Submesh\\(" glob:test_*.py output_mode=count`).
- Existing coupling patterns for mixed-domain boundaries: **2 `EquationBC(` occurrences** and **44 `intersect_measures` occurrences** (source: `rg "EquationBC\\(|intersect_measures" glob:test_*.py output_mode=count`).
- Recent history relevant to regression risk: **2 commits total**; latest adds `.loopy/*` docs, prior commit introduces all `test_submesh_*.py` examples (source: `git log --oneline -20`, `git show --stat --summary`).

## Goals
- Implement a Firedrake acoustic wave equation solver that supports Clayton A1 hybrid boundary conditions.
- Reuse the existing submesh/label/intersection-measure patterns to model an extended absorbing domain.
- Deliver automated tests that validate correctness, boundary coupling, and reduced boundary reflections.

## Non-Goals
- Rewriting Firedrake core `Submesh` internals.
- Implementing alternative absorbing boundary strategies (e.g., full PML) in this MVP.
- Building a production seismic workflow (inversion, I/O pipelines, visualization tooling).

## Users & Context
- Primary user: Computational scientist or numerical-method developer prototyping wave propagation in Firedrake.
- Secondary user(s): CI maintainers and developers extending the submesh example suite.
- Environment: Python/Firedrake/PETSc with pytest, including MPI-parallel test execution patterns already used in this repo.

## Scope
- In scope:
  - Add a new acoustic solver module (non-test Python file) and at least one usage/test entry point.
  - Define parent-domain + submesh extended-domain setup using labels and `Submesh`.
  - Implement Clayton A1 hybrid BC on designated boundary labels in weak form.
  - Couple solution fields across parent/submesh interfaces using `intersect_measures` and equation constraints.
  - Add automated tests for accuracy/sanity and absorbing-boundary behavior.
- Out of scope:
  - Full 3D production-scale performance tuning.
  - Mesh-generation tooling beyond existing test-style synthetic meshes.
  - Non-Clayton boundary condition variants.

## Data Sources
- `test_submesh_solve.py`: Solver setup, mixed-domain coupling, `EquationBC`, interface measures, convergence/sanity patterns.
- `test_submesh_assemble.py`: Assembly-level coupling and boundary-condition equation examples.
- `test_submesh_base.py`, `test_submesh_interpolate.py`, `test_submesh_assign.py`, `test_submesh_comm.py`, `test_submesh_facet.py`, `test_submesh_basics.py`: Submesh construction, labeling, interpolation/assignment, MPI behavior.
- Git history (`git log --oneline -20`, `git show --stat --summary`): Recent changes and regression context.
- Paper URL (`https://gmd.copernicus.org/articles/15/5857/2022/gmd-15-5857-2022.html`): Intended source for Clayton A1 definition; direct fetch was unavailable in-session due to permission denial.

## Requirements
### Functional
- [F1] Provide a callable Python solver interface for the acoustic wave equation on a Firedrake mesh with explicit inputs for wave speed, source term, timestep controls, and boundary labels.
- [F2] Build an extended absorbing domain via labeled regions and `Submesh` (pattern aligned with current tests using `DG0`, `mark_entities`, `Submesh`).
- [F3] Implement Clayton A1 hybrid boundary-condition terms on selected outer-boundary labels of the absorbing domain.
- [F4] Implement parent/submesh coupling terms using intersected measures (`dx/ds/dS` with `intersect_measures`) and enforce interface continuity/compatibility with equation-based constraints.
- [F5] Include at least one deterministic test case that verifies solver correctness against an analytic, manufactured, or controlled reference solution.
- [F6] Include at least one deterministic test case that compares reflective-vs-Clayton-A1 boundary behavior using the same setup and records a reflection metric.
- [F7] Support execution in the same pytest style used here (serial + MPI-marked tests where applicable).

### Non-Functional
- [N1] Performance: MVP benchmark case completes within CI-friendly runtime (target: ≤120 s for the default validation case on 1 process).
- [N2] Security/Privacy: Solver and tests must be self-contained, with no external network dependence at runtime.
- [N3] Accessibility: Public solver entry points must have clear docstrings describing parameters, boundary labels, and expected units/conventions.

## User Stories (MVP)
- As a numerical-method developer, I want to run an acoustic wave simulation with Clayton A1 boundaries on an extended submesh so that outgoing waves are absorbed with less artificial reflection.
- As a maintainer, I want automated tests proving boundary coupling and solver correctness so that future changes do not break submesh-based wave workflows.

## Success Metrics
- Add **≥1 non-test Python module** implementing the solver (baseline: 0 now).
- Add **≥2 acoustic-specific pytest tests** (baseline: 0 acoustic/Clayton references now).
- In the validation case, achieve bounded numerical error at final time (target L2 error threshold defined in tests and reproducible across runs).
- In reflective-vs-Clayton comparison, reduce measured reflected amplitude at monitor point(s) by a fixed threshold (target: ≥50% reduction) under identical mesh/source/time settings.
- Existing submesh example tests targeted by the implementation remain passing for unchanged behavior paths.

## Risks & Mitigations
- Clayton A1 formula ambiguity (paper unavailable in-session) → Require explicit equation reference (section/equation ID) in implementation notes and tests before merge.
- Interface sign/normal-orientation mistakes across parent/submesh terms → Add symmetry/sign regression tests modeled on existing `EquationBC` and interface-measure examples.
- Time-step instability (CFL violations) → Encode conservative default timestep and explicit stability checks in test setups.

## Open Questions
- Which exact Clayton A1 equation variant (and notation/sign convention) from the paper is required for MVP?
The first order wave equation considering the normal component of the velocity and the pressure, as described in the paper, is the intended target.
- Is MVP strictly 2D, or must 3D be included from the first implementation?
Only 2D.

## Assumptions
- Firedrake, PETSc, and MPI are available in the target environment indicated by the seed command (`venv-firedrake` activation path).
- MVP can start with 2D cases and extend later, because current repo examples already provide strong 2D submesh and interface patterns.
- Exact Clayton A1 coefficients and weak-form details are not derivable from local repository files; direct paper fetch was blocked in-session, so final implementation will require either accessible paper text or maintainer-provided formula details.