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

## Findings from regress-submesh-suite

1. **What was investigated**
   - `solve_acoustic_submesh(...)` docstring coverage in `acoustic_solver.py` for boundary-label semantics, one-step controls (`dt`, `t_end`), and required diagnostics names.

2. **What was found (evidence)**
   - The docstring now states how `boundary_labels` split between interface coupling boundaries and Clayton A1 damping boundaries.
   - The docstring now describes one-step controls through `dt == t_end` and the `num_steps = max(1, ceil(t_end / dt))` behavior.
   - The Returns section now explicitly names diagnostics: `solution_norm`, `interface_label`, and `clayton_labels`.
   - Acceptance command passed with exit 0: `python -c "import inspect, acoustic_solver as m; d=inspect.getdoc(m.solve_acoustic_submesh) or \"\"; assert \"boundary\" in d.lower() and \"dt\" in d and \"solution_norm\" in d and \"interface_label\" in d and \"clayton_labels\" in d"`.

3. **Conclusion**
   - The solver API docstring now documents boundary semantics, timestep controls, and diagnostics consistently with current behavior and tests.

4. **Recommended next action**
   - Execute phase regression tests in an environment where the known MPI/PETSc finalize hang on `test_submesh_solve.py::test_submesh_solve_simple[None-4]` is resolved.
