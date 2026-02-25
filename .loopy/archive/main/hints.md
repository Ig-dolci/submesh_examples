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

## Findings from verify
1. **What was investigated**
   - Re-ran `pytest test_submesh_acoustic.py` to confirm reflective-vs-Clayton norm ordering and API-focused acoustic tests in `test_submesh_acoustic.py`.
2. **What was found (with evidence)**
   - `test_solve_acoustic_submesh_reflection_clayton_reduces_norm` asserts `result_with_clayton["solution_norm"] <= result_reflective["solution_norm"]`.
   - API-focused tests (`test_solve_acoustic_submesh_api_manufactured_one_step`, parallel one-step finite norm, invalid-boundary-label guards, and non-2D mesh rejection) remained green.
   - Validation evidence: `pytest test_submesh_acoustic.py` completed with `7 passed in 9.38s`.
3. **Conclusion**
   - Reflective-vs-Clayton norm ordering and existing API-facing acoustic behavior are stable.
4. **Recommended next action**
   - Verify phase tasks are complete; continue with normal downstream CI/merge flow.
