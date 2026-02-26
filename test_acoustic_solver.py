from acoustic_solver import solve_acoustic_submesh


def test_clayton_a1_absorbing_term_disabled_when_no_absorbing_labels():
    result = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.3,
        outer_boundary_labels=(1, 2),
        interface_labels=(1, 2),
    )

    assert result["domain"]["absorbing_boundary_labels"] == ()
    assert result["domain"]["absorbing_term_enabled"] is False
    assert all(value == 0.0 for value in result["absorbing_contribution_trace"])


def test_clayton_a1_absorbing_term_enabled_when_labels_present():
    result = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.3,
        outer_boundary_labels=(1, 2, 3),
        interface_labels=(3,),
    )

    assert result["domain"]["absorbing_boundary_labels"] == (1, 2)
    assert result["domain"]["absorbing_term_enabled"] is True
    assert any(abs(value) > 0.0 for value in result["absorbing_contribution_trace"][1:])
