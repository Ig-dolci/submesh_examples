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


def test_ricker_source_is_time_varying_and_parameters_exposed():
    result = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.4,
        frequency_peak=2.0,
        amplitude=3.0,
        source_location=(0.2, 0.7),
    )

    source_values = result["source_values"]
    assert len(source_values) == int(round(result["parameters"]["final_time"] / result["parameters"]["dt"]))
    assert len({round(value, 12) for value in source_values}) > 1
    assert result["parameters"]["frequency_peak"] == 2.0
    assert result["parameters"]["amplitude"] == 3.0
    assert result["parameters"]["source_location"] == (0.2, 0.7)


def test_ricker_source_changes_with_frequency_peak():
    low_frequency = solve_acoustic_submesh(dt=0.05, final_time=0.4, frequency_peak=1.0)
    high_frequency = solve_acoustic_submesh(dt=0.05, final_time=0.4, frequency_peak=4.0)

    assert low_frequency["source_values"] != high_frequency["source_values"]
