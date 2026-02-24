# Follow-Up

Items below require future data or human action after the automated plan completes.
Review and execute these manually once the prerequisite conditions are met.

- [ ] analyze: when access to `https://gmd.copernicus.org/articles/15/5857/2022/gmd-15-5857-2022.html` is available, verify Clayton A1 coefficient/sign conventions in `acoustic_solver.py` and rerun `pytest -q test_submesh_solve.py -k "acoustic or clayton"`.
- [ ] measure: after at least 10 CI runs on main, compare p50/p95 duration of `test_submesh_solve.py` against pre-change baseline to confirm the new acoustic tests stay within the 60s target.
