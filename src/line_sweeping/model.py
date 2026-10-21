# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""MILP model of the line sweeping problem, solved with OR-Tools and SCIP.

Constraint numbers refer to docs/mip-model.md.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ortools.linear_solver import pywraplp

from line_sweeping.court import Point, distance
from line_sweeping.instance import SweepInstance
from line_sweeping.solution import Move, MoveKind, Status, SweepPlan

_STATUS = {
    pywraplp.Solver.OPTIMAL: Status.OPTIMAL,
    pywraplp.Solver.FEASIBLE: Status.FEASIBLE,
    pywraplp.Solver.INFEASIBLE: Status.INFEASIBLE,
}


@dataclass
class _Model:
    solver: pywraplp.Solver
    instance: SweepInstance
    points: list[Point]  # line vertices 0 … n−1, the broom place B is node n
    s: dict[int, pywraplp.Variable]
    w: dict[tuple[int, int], pywraplp.Variable]

    @property
    def broom(self) -> int:
        return len(self.points) - 1


def build_model(instance: SweepInstance, pair_cuts: bool = True) -> _Model:
    """Build the model for one instance."""
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("SCIP solver is not available in this OR-Tools build")

    graph = instance.graph
    v_s, v_c = instance.sweep_speed, instance.carry_speed
    vertices = range(len(graph.vertices))
    points = [v.point for v in graph.vertices] + [instance.broom]
    broom = len(points) - 1
    nodes = range(len(points))

    # Decision variables.
    # s(e) = 1: segment e is swept from u(e) to v(e); 0: from v(e) to u(e).
    s = {e: solver.BoolVar(f"s[{e}]") for e in range(len(graph.segments))}
    # w(a, b) = 1: the broom is carried straight from node a to node b once.
    w = {(a, b): solver.BoolVar(f"w[{a},{b}]") for a in nodes for b in nodes if a != b}

    out_sweep: dict[int, list] = defaultdict(list)
    in_sweep: dict[int, list] = defaultdict(list)
    for e, seg in enumerate(graph.segments):
        out_sweep[seg.u].append(s[e])
        in_sweep[seg.v].append(s[e])
        out_sweep[seg.v].append(1 - s[e])
        in_sweep[seg.u].append(1 - s[e])

    def carries_out(a: int) -> pywraplp.LinearExpr:
        return solver.Sum(w[a, b] for b in nodes if b != a)

    def carries_in(b: int) -> pywraplp.LinearExpr:
        return solver.Sum(w[a, b] for a in nodes if a != b)

    for v in vertices:
        # (1) every vertex is left as often as it is reached.
        solver.Add(solver.Sum(out_sweep[v]) + carries_out(v) == solver.Sum(in_sweep[v]) + carries_in(v))
    # (2) the broom is picked up once and put back once.
    solver.Add(carries_out(broom) == 1)
    solver.Add(carries_in(broom) == 1)
    for v in graph.odd_vertices:
        # (3) a sweeping run starts or ends at every vertex of odd degree.
        solver.Add(carries_out(v) + carries_in(v) >= 1)
    if pair_cuts:
        for a in vertices:
            for b in vertices:
                if a < b:
                    # (4) never carry the broom back and forth between two vertices.
                    solver.Add(w[a, b] + w[b, a] <= 1)

    # Objective: sweeping time (a constant) + carrying time.
    carry_time = solver.Sum(distance(points[a], points[b]) / v_c * var for (a, b), var in w.items())
    solver.Minimize(carry_time + graph.total_length / v_s)

    return _Model(solver, instance, points, s, w)


def _euler_route(model: _Model) -> list[Move]:
    """Euler circuit of the sweep and carry arcs, starting at the broom place."""
    graph = model.instance.graph
    arcs: dict[int, list[tuple[int, MoveKind, str | None]]] = defaultdict(list)
    for (a, b), var in model.w.items():
        if var.solution_value() > 0.5:
            arcs[a].append((b, MoveKind.CARRY, None))
    for e, seg in enumerate(graph.segments):
        a, b = (seg.u, seg.v) if model.s[e].solution_value() > 0.5 else (seg.v, seg.u)
        arcs[a].append((b, MoveKind.SWEEP, seg.line))
    for out in arcs.values():
        # Popped from the end: sweep arcs first, so that runs stay long.
        out.sort(key=lambda arc: (arc[1] == MoveKind.SWEEP, -arc[0]))

    # Hierholzer's algorithm.
    stack: list[tuple[int, tuple[int, MoveKind, str | None] | None]] = [(model.broom, None)]
    circuit: list[tuple[int, int, MoveKind, str | None]] = []
    while stack:
        node, _ = stack[-1]
        if arcs[node]:
            arc = arcs[node].pop()
            stack.append((arc[0], arc))
        else:
            _, arc = stack.pop()
            if arc is not None:
                circuit.append((stack[-1][0], *arc))
    circuit.reverse()

    pts = model.points
    moves = [Move(kind, pts[a], pts[b], line) for a, b, kind, line in circuit]
    return _merge_carries(moves)


def _merge_carries(moves: list[Move]) -> list[Move]:
    """Join consecutive carries into one straight carry where that costs nothing extra."""
    merged: list[Move] = []
    for move in moves:
        if merged and move.kind == merged[-1].kind == MoveKind.CARRY:
            previous = merged[-1]
            direct = distance(previous.start, move.end)
            if abs(previous.length + move.length - direct) <= 1e-9:
                merged[-1] = Move(MoveKind.CARRY, previous.start, move.end)
                continue
        merged.append(move)
    return merged


def solve(instance: SweepInstance, time_limit_s: float | None = None, pair_cuts: bool = True) -> SweepPlan:
    """Build and solve the model."""
    model = build_model(instance, pair_cuts)
    if time_limit_s is not None:
        model.solver.SetTimeLimit(int(time_limit_s * 1000))
    status = _STATUS.get(model.solver.Solve(), Status.UNKNOWN)
    if status not in (Status.OPTIMAL, Status.FEASIBLE):
        return SweepPlan(status)
    return SweepPlan(status, _euler_route(model), model.solver.Objective().Value())


def model_size(instance: SweepInstance) -> dict[str, int]:
    """Size of the model."""
    model = build_model(instance)
    return {
        "vertices": len(instance.graph.vertices),
        "segments": len(instance.graph.segments),
        "binary variables s": len(model.s),
        "binary variables w": len(model.w),
        "constraints": model.solver.NumConstraints(),
    }
