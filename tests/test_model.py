# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

from functools import cache

import pytest

from line_sweeping import CourtDimensions, Move, MoveKind, Status, SweepInstance, SweepPlan, solve, verify
from line_sweeping.court import distance

BEHIND_CENTRE = (5.485, -6.40)  # back fence, behind the centre mark
SIDE_NEAR_NET = (-3.66, 11.0)  # side fence, next to the net post
BROOM_PLACES = [BEHIND_CENTRE, SIDE_NEAR_NET, (-1.0, -1.0), (0.0, 0.0), (5.485, 5.485), (20.0, 30.0)]


def optimal_carry_distance(instance: SweepInstance) -> float:
    """Exact minimal carrying distance, computed without the MILP.

    The carries together with the lines must form an Euler circuit through
    the broom place B. B is joined to two vertices u, v (possibly u = v);
    the remaining carries form a T-join for the vertices of odd degree,
    toggled by u and v. With straight-line distances a minimal T-join is a
    minimal perfect matching, found here by dynamic programming over subsets.
    """
    graph = instance.graph
    points = [v.point for v in graph.vertices]
    odd = frozenset(graph.odd_vertices)

    @cache
    def matching(rest: frozenset[int]) -> float:
        if not rest:
            return 0.0
        first, *others = sorted(rest)
        return min(distance(points[first], points[k]) + matching(rest - {first, k}) for k in others)

    best = float("inf")
    for u in range(len(points)):
        for v in range(u, len(points)):
            ends = odd ^ {u} ^ {v} if u != v else odd
            cost = distance(instance.broom, points[u]) + distance(instance.broom, points[v]) + matching(ends)
            best = min(best, cost)
    return best


def test_half_court_graph():
    graph = SweepInstance(broom=BEHIND_CENTRE).graph
    assert len(graph.vertices) == 14
    assert len(graph.segments) == 14
    assert graph.total_length == pytest.approx(10.97 + 4 * 11.885 + 8.23 + 6.40 + 0.10)
    assert len(graph.odd_vertices) == 12
    kinds = sorted(v.kind for v in graph.vertices)
    assert kinds.count("corner") == 2 and kinds.count("junction") == 6 and kinds.count("line end") == 6


@pytest.mark.parametrize("broom", BROOM_PLACES)
def test_optimal_and_valid(broom):
    instance = SweepInstance(broom=broom)
    plan = solve(instance)

    assert plan.status == Status.OPTIMAL
    assert verify(instance, plan) == []
    assert plan.sweep_distance == pytest.approx(instance.sweep_length)
    assert plan.carry_distance == pytest.approx(optimal_carry_distance(instance))
    assert plan.objective == pytest.approx(instance.sweep_time + plan.carry_distance)
    assert len(plan.runs) >= instance.min_runs


def test_default_example():
    plan = solve(SweepInstance(broom=BEHIND_CENTRE))
    assert len(plan.runs) == 6
    assert plan.objective == pytest.approx(103.02, abs=0.01)


def test_speeds_scale_the_two_parts():
    base = solve(SweepInstance(broom=SIDE_NEAR_NET))
    instance = SweepInstance(broom=SIDE_NEAR_NET, sweep_speed=0.5, carry_speed=2.0)
    plan = solve(instance)
    assert verify(instance, plan) == []
    assert plan.carry_distance == pytest.approx(base.carry_distance)
    assert plan.objective == pytest.approx(2 * instance.sweep_length + base.carry_distance / 2)


def test_without_pair_cuts_same_optimum():
    instance = SweepInstance(broom=SIDE_NEAR_NET)
    assert solve(instance, pair_cuts=False).objective == pytest.approx(solve(instance).objective)


def test_singles_court_without_alleys():
    # Doubles width = singles width: the singles sidelines coincide with the doubles ones.
    court = CourtDimensions(doubles_width=8.23, singles_width=8.23)
    instance = SweepInstance(broom=BEHIND_CENTRE, court=court)
    plan = solve(instance)
    assert verify(instance, plan) == []
    assert plan.carry_distance == pytest.approx(optimal_carry_distance(instance))


def _sweep(a, b, line=None):
    return Move(MoveKind.SWEEP, a, b, line)


def _carry(a, b):
    return Move(MoveKind.CARRY, a, b)


def test_verify_detects_line_swept_twice_and_missing_lines():
    instance = SweepInstance(broom=(-1.0, -1.0))
    plan = SweepPlan(
        Status.FEASIBLE,
        [_carry((-1.0, -1.0), (0.0, 0.0)), _sweep((0.0, 0.0), (1.37, 0.0)), _sweep((1.37, 0.0), (0.0, 0.0)),
         _carry((0.0, 0.0), (-1.0, -1.0))],
    )
    errors = verify(instance, plan)
    assert any("swept twice" in e for e in errors)
    assert any("left doubles sideline is not swept" in e for e in errors)


def test_verify_detects_sweep_off_stop_points_and_missing_return():
    instance = SweepInstance(broom=(-1.0, -1.0))
    plan = SweepPlan(Status.FEASIBLE, [_carry((-1.0, -1.0), (0.0, 0.0)), _sweep((0.0, 0.0), (0.5, 0.0))])
    errors = verify(instance, plan)
    assert any("corner, junction or line end" in e for e in errors)
    assert any("returned" in e for e in errors)


def test_invalid_instance_rejected():
    with pytest.raises(ValueError):
        SweepInstance(broom=(0.0, 0.0), carry_speed=0.0)
    with pytest.raises(ValueError):
        CourtDimensions(singles_width=12.0)
