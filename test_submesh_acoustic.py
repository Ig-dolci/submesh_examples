import math

from firedrake import UnitSquareMesh

from acoustic_solver import solve_acoustic_submesh


def test_solve_acoustic_submesh_api_manufactured_one_step():
    mesh = UnitSquareMesh(8, 8)
    result = solve_acoustic_submesh(
        mesh=mesh,
        source=1.0,
        wave_speed=1.0,
        dt=0.01,
        t_end=0.01,
        boundary_labels=(1, 2, 3, 4),
    )
    assert result["num_steps"] == 1
    assert math.isfinite(result["solution_norm"])
    assert result["interface_label"] == (5,)


def test_solve_acoustic_submesh_reflection_clayton_reduces_norm():
    params = {"source": 1.0, "wave_speed": 1.0, "dt": 0.01, "t_end": 0.2}
    result_reflective = solve_acoustic_submesh(
        mesh=UnitSquareMesh(8, 8),
        boundary_labels=(5,),
        **params,
    )
    result_with_clayton = solve_acoustic_submesh(
        mesh=UnitSquareMesh(8, 8),
        boundary_labels=(2, 3, 4),
        **params,
    )

    assert result_reflective["clayton_labels"] == ()
    assert result_with_clayton["clayton_labels"] == (2, 3, 4)
    assert result_with_clayton["solution_norm"] <= result_reflective["solution_norm"]
