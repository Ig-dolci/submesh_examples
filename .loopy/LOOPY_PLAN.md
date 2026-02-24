---
agent_command: copilot --allow-all
test_command: pytest -q
max_iterations: 50
max_minutes: 240
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

<!-- loopy:seed ● Todo added: Scan project files

● Grep "acoustic|Clayton|A1|hybrid|hibrid|submesh|wave equation|extended domain"
  └ 209 lines found

● Glob "*"
  └ 8 files found

● Show recent commit history
  $ git --no-pager log --oneline -20
  └ 3 lines...

● List directory .
  └ 9 files found

● Read test_submesh_assemble.py lines 1-120
  └ 120 lines read

● Read test_submesh_solve.py lines 1-140
  └ 140 lines read

● Read test_submesh_base.py lines 1-130
  └ 130 lines read

● Read test_submesh_interpolate.py lines 1-120
  └ 120 lines read

● Read test_submesh_assign.py lines 1-120
  └ 120 lines read

● Read test_submesh_comm.py lines 1-120
  └ 98 lines read

● Read test_submesh_basics.py lines 1-120
  └ 16 lines read

● Read test_submesh_facet.py lines 1-140
  └ 124 lines read

● Todo started:

✗ Create session plan file
  $ cat > /Users/ddolci/.copilot/session-state/a2e8ede6-3571-48e7-b8be-04e6a9cc53ee/plan.md
  <<'EOF'
  # Plan
  1. Gather repository evidence (files, keywords, recent commits, measurable baselines).
  2. Synthesize constraints and requirements for an acoustic wave solver using submesh and ...
  Permission denied and could not request permission from user

● Glob "**/*.py"
  └ 8 files found

● Grep "\bSubmesh\b"
  └ 8 files found

● Grep "^def test_" in test_*.py
  └ 8 files found

● Grep "acoustic|Clayton|A1|hibrid|hybrid"
  └ No matches found

● Show recent commits with touched files
  $ git --no-pager log --oneline --name-only -20
  └ 17 lines...

✗ Compute baseline repository metrics
  $ python - <<'PY'
  from pathlib import Path
  import re
  root=Path('/Users/ddolci/dev_code/submesh_examples')
  files=sorted(root.glob('test_*.py'))...
  Permission denied and could not request permission from user

● Read test_submesh_solve.py lines 220-340
  └ 121 lines read

● Read test_submesh_assemble.py lines 260-360
  └ 101 lines read

● Read test_submesh_solve.py lines 420-560
  └ 141 lines read

● Inspect recent commit contents
  $ git --no-pager show --oneline --name-only --stat 10fc439 && echo '---' && git --no-pager show
  --oneline --name-only --stat 7423eb9
  └ 18 lines...

● Todo completed: search-seed-keywords, review-git-history

✗ web_fetch: https://gmd.copernicus.org/articles/15/5857/2022/gmd-15-5857-2022.html
  Permission denied and could not request permission from user

✗ Read .loopy/PRD.md
  Path does not exist

✗ Read .loopy/PROMPT.md
  Path does not exist

✗ Read .loopy/FOLLOW_UP.md
  Path does not exist

● List files including hidden files
  $ ls -la
  └ 13 lines...

● Check if recent commits added or removed files
  $ git --no-pager show --stat --summary --oneline 7423eb9 && echo '---' && git --no-pager show
  --stat --summary --oneline 10fc439
  └ 34 lines...

● Check working tree status
  $ git --no-pager status --short
  └ 7 lines...

● Compute key baseline counts
  $ rg '^def test_' test_*.py | wc -l && rg -o '\bSubmesh\b' test_*.py | wc -l && (rg -i
  'acoustic|clayton|hibrid|hybrid|wave equation' test_*.py || true) | wc -l && rg
  '@pytest\.mark\.parallel' test_*.py | wc -l
  └ 9 lines...

● Count tests and keyword baselines with grep
  $ grep -h '^def test_' test_*.py | wc -l && grep -Rho '\bSubmesh\b' test_*.py | wc -l && grep
  -RhoiE 'acoustic|clayton|hibrid|hybrid|wave equation' test_*.py | wc -l && grep -Rho
  '@pytest.mark.parallel' test_*.py | wc -l
  └ 5 lines...

✗ Count test function definitions per file
  $ for f in test_*.py; do printf '%s ' "$f"; grep -c '^def test_' "$f"; done
  Permission denied and could not request permission from user

● Grep "_solve_helmholtz|EquationBC|Submesh\(|intersect_measures|DirichletBC\(|solve\("
(/Users/ddolci/dev_code/submesh_examples/test_submesh_solve.py)
  └ 60 lines found

● Grep "EquationBC|Submesh\(|intersect_measures|DirichletBC\(|solve\("
(/Users/ddolci/dev_code/submesh_examples/test_submesh_assemble.py)
  └ 39 lines found

● Grep "from firedrake import \*|import pytest|petsc4py|firedrake" in test_*.py
(/Users/ddolci/dev_code/submesh_examples)
  └ 23 lines found

● Grep "^def test_" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 8 files found

● Grep "Submesh\(" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 8 files found

● Grep "EquationBC\(" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 2 files found

● Grep "intersect_measures" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 2 files found

● Grep "@pytest\.mark\.parallel\(nprocs=\d+\)|@pytest\.mark\.parallel\(\[\d+, \d+\]\)" in test_*.py
(/Users/ddolci/dev_code/submesh_examples)
  └ 38 lines found

● Grep "@pytest\.mark\.parallel" in test_*.py (/Users/ddolci/dev_code/submesh_examples)
  └ 7 files found

● Glob "*.md" in /Users/ddolci/dev_code/submesh_examples
  └ No matches found

● Grep "acoustic|Clayton|A1|hibrid|hybrid" (/Users/ddolci/dev_code/submesh_examples)
  └ No matches found

● Todo started: draft-prd

● Todo queried:

● Todo completed: draft-prd

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
- Deliver agent-executable tests that validate correctness, boundary coupling, and reduced boundary reflections.

## Non-Goals
- Rewriting Firedrake core `Submesh` internals.
- Implementing alternative absorbing boundary strategies (e.g., full PML) in this MVP.
- Building a production seismic workflow (inversion, I/O pipelines, visualization tooling).

## Users & Context
- Primary user: Computational scientist or numerical-method developer prototyping wave propagation in Firedrake.
- Secondary user(s): Code agents and CI maintainers extending the submesh example suite.
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
- Paper URL (`https://gmd.copernicus.org/articles/15/5857/2022/gmd-15-5857-2022.html`): Intended source for Clayton A1 definition, but direct fetch was unavailable in-session due permission denial.

## Requirements
### Functional
- [F1] Provide a callable Python solver interface for the acoustic wave equation on a Firedrake mesh with explicit inputs for wave speed, source term, timestep controls, and boundary labels.
- [F2] Build an extended absorbing domain via labeled regions and `Submesh` (pattern aligned with current tests using `DG0`, `mark_entities`, `Submesh`).
- [F3] Implement Clayton A1 hybrid boundary-condition terms on selected outer-boundary labels of the absorbing domain.
- [F4] Implement parent/submesh coupling terms using intersected measures (`dx/ds/dS` with `intersect_measures`) and enforce interface continuity/compatibility with equation-based constraints.
- [F5] Include at least one deterministic test case that verifies solver correctness against an analytic/manufactured or controlled reference solution.
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
- Is MVP strictly 2D, or must 3D be included from the first implementation?
- What source wavelet and receiver diagnostics should be standardized for reflection metrics?
- Should solver output be an in-memory field only, or include optional file export hooks?

## Assumptions
- Firedrake, PETSc, and MPI are available in the target environment indicated by the seed command (`venv-firedrake` activation path).
- MVP can start with 2D cases and extend later, because current repo examples already provide strong 2D submesh and interface patterns.
- Exact Clayton A1 coefficients/weak-form details are not derivable from local repository files; direct paper fetch was blocked in-session, so final implementation will require either accessible paper text or maintainer-provided formula details. -->

## Phase: implement-acoustic-solver
<!-- loopy:phase implement-acoustic-solver -->

- [ ] add: create acoustic_solver.py with a public solve_acoustic_submesh(...) API and parameter docstring covering mesh, source, wave speed, dt, t_end, and boundary labels — Acceptance: python -c "import acoustic_solver as m; assert callable(m.solve_acoustic_submesh)" exits 0.
- [ ] implement: add extended-domain construction helper in acoustic_solver.py using DG0 labeling plus Submesh(...) patterns from test_submesh_base.py and test_submesh_assign.py — Acceptance: a solver smoke path builds a Submesh with num_cells() > 0 on UnitSquareMesh.
- [ ] implement: assemble weak-form coupling in acoustic_solver.py using intersect_measures and EquationBC patterns from test_submesh_solve.py and test_submesh_assemble.py, including Clayton A1 hybrid term on selected ds labels — Acceptance: a one-step solve returns a finite norm and no Firedrake/PETSc error.

## Phase: add-acoustic-tests
<!-- loopy:phase add-acoustic-tests -->

- [ ] add: create test_submesh_acoustic.py with a manufactured-solution correctness test for solve_acoustic_submesh(...) — Acceptance: pytest -q test_submesh_acoustic.py -k manufactured passes with an explicit L2 error threshold assertion.
- [ ] add: create a reflective-vs-Clayton comparison test in test_submesh_acoustic.py using identical mesh/source/time settings and a monitor metric — Acceptance: pytest -q test_submesh_acoustic.py -k reflection passes and asserts reflected_amplitude_ratio <= 0.5.
- [ ] add: create an MPI-marked compatibility test in test_submesh_acoustic.py using @pytest.mark.parallel style from test_submesh_solve.py and test_submesh_comm.py — Acceptance: pytest -q test_submesh_acoustic.py -k parallel passes in MPI-enabled runs.

## Phase: regress-submesh-suite
<!-- loopy:phase regress-submesh-suite -->

- [ ] verify: run regression tests for existing coupling examples in test_submesh_assemble.py and test_submesh_solve.py after adding the new module and tests — Acceptance: pytest -q test_submesh_assemble.py test_submesh_solve.py exits 0.
- [ ] verify: run repository keyword scan for acoustic|Clayton|A1|wave equation to confirm intentional feature footprint — Acceptance: rg -n -i "acoustic|clayton|a1|wave equation" . shows matches in acoustic_solver.py and test_submesh_acoustic.py.
- [ ] update: finalize solver docstrings in acoustic_solver.py to state boundary-label semantics and units conventions used by the API — Acceptance: python -c "import inspect, acoustic_solver as m; d=inspect.getdoc(m.solve_acoustic_submesh) or \"\"; assert \"boundary\" in d.lower() and \"dt\" in d" exits 0.
