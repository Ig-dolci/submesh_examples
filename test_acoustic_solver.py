import math

from firedrake import RectangleMesh

from acoustic_solver import solve_acoustic_submesh


def test_solve_acoustic_submesh_returns_finite_norm():
    result = solve_acoustic_submesh(
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        source=1.0,
        wave_speed=1.0,
        dt=0.01,
        t_end=0.01,
        boundary_labels=(1, 2, 3, 4),
    )
    assert math.isfinite(result["solution_norm"])


def test_solve_acoustic_submesh_interface_label_rectangle_baseline():
    result = solve_acoustic_submesh(
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        source=1.0,
        wave_speed=1.0,
        dt=0.01,
        t_end=0.01,
        boundary_labels=(1, 2, 3, 4),
    )
    assert result["interface_label"] == (5,)


def test_solve_acoustic_submesh_reflective_norm_not_below_clayton():
    params = {"source": 1.0, "wave_speed": 1.0, "dt": 0.01, "t_end": 0.2}
    reflective = solve_acoustic_submesh(
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        boundary_labels=(5,),
        **params,
    )
    clayton = solve_acoustic_submesh(
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        boundary_labels=(2, 3, 4),
        **params,
    )
    assert reflective["solution_norm"] >= clayton["solution_norm"]
