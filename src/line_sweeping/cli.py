# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""Command line interface: solve one instance and print the route."""

from __future__ import annotations

import argparse
import sys

from line_sweeping.court import Point
from line_sweeping.instance import SweepInstance
from line_sweeping.model import solve
from line_sweeping.solution import MoveKind, SweepPlan, verify


def _pt(p: Point) -> str:
    return f"({p[0] + 0.0:.3f}, {p[1] + 0.0:.3f})"  # + 0.0 turns -0.0 into 0.0


def format_plan(instance: SweepInstance, plan: SweepPlan) -> str:
    lines = [f"status: {plan.status.value}"]
    if not plan.has_plan:
        return "\n".join(lines)

    carry_time = plan.carry_distance / instance.carry_speed
    lines.append(
        f"total time: {plan.objective:.2f} s = sweeping {instance.sweep_time:.2f} s"
        f" + carrying {carry_time:.2f} s"
    )
    lines.append(
        f"distance: sweeping {plan.sweep_distance:.2f} m, carrying {plan.carry_distance:.2f} m;"
        f" {len(plan.runs)} runs (at least {instance.min_runs})"
    )
    run, run_open = 0, False
    for move in plan.moves:
        if move.kind == MoveKind.CARRY:
            lines.append(f"  carry  {_pt(move.start)} → {_pt(move.end)}   {move.length:7.3f} m")
            run_open = False
            continue
        if not run_open:
            run += 1
            lines.append(f"run {run}:")
            run_open = True
        lines.append(f"  sweep  {_pt(move.start)} → {_pt(move.end)}   {move.length:7.3f} m   {move.line}")

    errors = verify(instance, plan)
    lines.append("check: OK" if not errors else "check FAILED:\n  " + "\n  ".join(errors))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plan sweeping the lines of one half of a clay tennis court.")
    parser.add_argument("--broom-x", "-x", type=float, required=True,
                        help="x of the broom place [m]; 0 = left doubles sideline, x grows to the right")
    parser.add_argument("--broom-y", "-y", type=float, required=True,
                        help="y of the broom place [m]; 0 = baseline, y grows towards the net")
    parser.add_argument("--sweep-speed", type=float, default=1.0, help="speed while sweeping v_s [m/s]")
    parser.add_argument("--carry-speed", type=float, default=1.0, help="speed while carrying v_c [m/s]")
    parser.add_argument("--time-limit", type=float, help="time limit of the solver [s]")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page

    instance = SweepInstance(
        broom=(args.broom_x, args.broom_y),
        sweep_speed=args.sweep_speed,
        carry_speed=args.carry_speed,
    )
    print(format_plan(instance, solve(instance, args.time_limit)))


if __name__ == "__main__":
    main()
