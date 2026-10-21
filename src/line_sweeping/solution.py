# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""Sweeping plan returned by the model and an independent feasibility check."""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field

from line_sweeping.court import Line, Point, distance, stop_points
from line_sweeping.instance import SweepInstance

TOLERANCE = 1e-6


class Status(enum.Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"


class MoveKind(enum.Enum):
    SWEEP = "sweep"
    CARRY = "carry"


@dataclass(frozen=True)
class Move:
    """One straight move of the worker: sweeping a line segment or carrying the broom."""

    kind: MoveKind
    start: Point
    end: Point
    line: str | None = None

    @property
    def length(self) -> float:
        return distance(self.start, self.end)


@dataclass
class SweepPlan:
    """Result of one solver run.

    Attributes:
        status: solver status.
        moves: the route from picking up the broom to putting it back, in order.
        objective: total time in seconds as reported by the solver, or None without a plan.
    """

    status: Status
    moves: list[Move] = field(default_factory=list)
    objective: float | None = None

    @property
    def has_plan(self) -> bool:
        return self.status in (Status.OPTIMAL, Status.FEASIBLE)

    @property
    def runs(self) -> list[list[Move]]:
        """Sweeping runs: maximal sequences of sweep moves without lifting the broom."""
        runs: list[list[Move]] = []
        previous = MoveKind.CARRY
        for move in self.moves:
            if move.kind == MoveKind.SWEEP:
                if previous == MoveKind.CARRY:
                    runs.append([])
                runs[-1].append(move)
            previous = move.kind
        return runs

    @property
    def carries(self) -> list[Move]:
        return [m for m in self.moves if m.kind == MoveKind.CARRY]

    @property
    def sweep_distance(self) -> float:
        return sum(m.length for m in self.moves if m.kind == MoveKind.SWEEP)

    @property
    def carry_distance(self) -> float:
        return sum(m.length for m in self.carries)


def route_time(instance: SweepInstance, moves: list[Move]) -> float:
    """Total time of a route: sweeping at v_s, carrying at v_c."""
    speed = {MoveKind.SWEEP: instance.sweep_speed, MoveKind.CARRY: instance.carry_speed}
    return sum(m.length / speed[m.kind] for m in moves)


def _position_on(p: Point, line: Line, tol: float) -> float | None:
    """Distance of p from line.start along the line, or None if p is not on the line."""
    (x1, y1), (x2, y2) = line.start, line.end
    length = line.length
    s = ((p[0] - x1) * (x2 - x1) + (p[1] - y1) * (y2 - y1)) / length
    if not -tol <= s <= length + tol:
        return None
    foot = (x1 + s / length * (x2 - x1), y1 + s / length * (y2 - y1))
    return s if distance(p, foot) <= tol else None


def verify(instance: SweepInstance, plan: SweepPlan, tol: float = TOLERANCE) -> list[str]:
    """Check a plan against the rules of the problem statement.

    Works only with positions and the painted lines, independently of the
    model's graph and indices. Returns a list of violated rules; an empty
    list means the plan is valid.
    """
    moves = plan.moves
    if not moves:
        return ["plan has no moves"]
    errors: list[str] = []
    broom = instance.broom

    if distance(moves[0].start, broom) > tol:
        errors.append("the route must start where the broom is kept")
    if distance(moves[-1].end, broom) > tol:
        errors.append("the broom must be returned to its place")
    if moves[0].kind != MoveKind.CARRY or moves[-1].kind != MoveKind.CARRY:
        errors.append("the broom must be carried from its place and back to it")
    for previous, move in zip(moves, moves[1:]):
        if distance(previous.end, move.start) > tol:
            errors.append(f"the route jumps from {_fmt(previous.end)} to {_fmt(move.start)}")

    stops = stop_points(instance.lines)

    def is_stop(p: Point) -> bool:
        return any(distance(p, q) <= tol for q in stops)

    # Swept intervals along each painted line, as distances from its start.
    swept: dict[str, list[tuple[float, float]]] = {line.name: [] for line in instance.lines}
    for move in moves:
        if move.kind != MoveKind.SWEEP:
            continue
        where = f"sweep {_fmt(move.start)} → {_fmt(move.end)}"
        if not (is_stop(move.start) and is_stop(move.end)):
            errors.append(f"{where} does not start and end at a corner, junction or line end")
        hits = [
            (line, a, b)
            for line in instance.lines
            if (a := _position_on(move.start, line, tol)) is not None
            and (b := _position_on(move.end, line, tol)) is not None
        ]
        if not hits:
            errors.append(f"{where} does not follow a line")
            continue
        line, a, b = hits[0]
        if move.line is not None and move.line != line.name:
            errors.append(f"{where} is on {line.name}, not on {move.line}")
        swept[line.name].append((min(a, b), max(a, b)))

    for line in instance.lines:
        reached = 0.0
        for a, b in sorted(swept[line.name]):
            if a < reached - tol:
                errors.append(f"{line.name} is swept twice around {a:.3f} m from its start")
            elif a > reached + tol:
                errors.append(f"{line.name} is not swept between {reached:.3f} and {a:.3f} m")
            reached = max(reached, b)
        if reached < line.length - tol:
            errors.append(f"{line.name} is not swept between {reached:.3f} and {line.length:.3f} m")

    if plan.objective is not None and not math.isclose(
        route_time(instance, moves), plan.objective, rel_tol=1e-6, abs_tol=1e-6
    ):
        errors.append("the route time differs from the objective value")
    return errors


def _fmt(p: Point) -> str:
    return f"({p[0]:.3f}, {p[1]:.3f})"
