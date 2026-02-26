# Follow-Up

Items below require future data or human action after the automated plan completes.
Review and execute these manually once the prerequisite conditions are met.

- [ ] After Firedrake-enabled CI/environment access is available, execute full `pytest -q` for all `test_*.py` and confirm no regressions outside acoustic/submesh slices.
- [ ] After identifying the canonical tutorial variant, validate temporal/spatial source expression in `acoustic_solver.py` against that reference and update tests if formula constants differ.
