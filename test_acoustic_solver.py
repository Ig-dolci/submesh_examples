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


def test_api_contract_records_source_and_time_parameters():
    result = solve_acoustic_submesh(
        dt=0.025,
        final_time=0.25,
        frequency_peak=3.0,
        amplitude=1.5,
        source_location=(0.1, 0.9),
    )

    parameters = result["parameters"]
    assert parameters["dt"] == 0.025
    assert parameters["final_time"] == 0.25
    assert parameters["frequency_peak"] == 3.0
    assert parameters["amplitude"] == 1.5
    assert parameters["source_location"] == (0.1, 0.9)


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
    absorbing_low_frequency = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.4,
        frequency_peak=1.0,
        outer_boundary_labels=(1, 2, 3),
        interface_labels=(3,),
    )
    absorbing_high_frequency = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.4,
        frequency_peak=4.0,
        outer_boundary_labels=(1, 2, 3),
        interface_labels=(3,),
    )
    reflective_low_frequency = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.4,
        frequency_peak=1.0,
        outer_boundary_labels=(1, 2),
        interface_labels=(1, 2),
    )
    reflective_high_frequency = solve_acoustic_submesh(
        dt=0.05,
        final_time=0.4,
        frequency_peak=4.0,
        outer_boundary_labels=(1, 2),
        interface_labels=(1, 2),
    )

    assert absorbing_low_frequency["source_values"] != absorbing_high_frequency["source_values"]
    assert reflective_low_frequency["source_values"] != reflective_high_frequency["source_values"]
    assert absorbing_low_frequency["domain"]["absorbing_term_enabled"] is True
    assert reflective_low_frequency["domain"]["absorbing_term_enabled"] is False
