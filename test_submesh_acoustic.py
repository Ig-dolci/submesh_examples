import math

import pytest
from firedrake import RectangleMesh

from acoustic_solver import solve_acoustic_submesh


def test_solve_acoustic_submesh_api_manufactured_one_step():
    mesh = RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True)
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
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        boundary_labels=(5,),
        **params,
    )
    result_with_clayton = solve_acoustic_submesh(
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        boundary_labels=(2, 3, 4),
        **params,
    )

    assert result_reflective["clayton_labels"] == ()
    assert result_with_clayton["clayton_labels"] == (2, 3, 4)
    assert result_with_clayton["solution_norm"] <= result_reflective["solution_norm"]


@pytest.mark.parallel([1, 3])
def test_solve_acoustic_submesh_parallel_one_step_finite_norm():
    result = solve_acoustic_submesh(
        mesh=RectangleMesh(8, 8, 1.0, 1.0, quadrilateral=True),
        source=1.0,
        wave_speed=1.0,
        dt=0.01,
        t_end=0.01,
        boundary_labels=(1, 2, 3, 4),
    )
    assert result["num_steps"] == 1
    assert math.isfinite(result["solution_norm"])


def test_solve_acoustic_submesh_rejects_non_2d_mesh():
    class FakeMesh3D:
        @staticmethod
        def topological_dimension():
            return 3

    with pytest.raises(ValueError, match=r"mesh\.topological_dimension\(\) must be 2"):
        solve_acoustic_submesh(
            mesh=FakeMesh3D(),
            source=1.0,
            wave_speed=1.0,
            dt=0.01,
            t_end=0.01,
            boundary_labels=(1,),
        )
