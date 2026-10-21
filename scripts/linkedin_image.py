# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""Render the LinkedIn image from two solved example instances."""

from __future__ import annotations

import sys
from pathlib import Path

from line_sweeping import SweepInstance, solve, verify
from line_sweeping.draw import draw_linkedin

OUTPUT = Path(__file__).resolve().parent.parent / "images" / "line-sweeping-linkedin.png"


def solved(instance: SweepInstance):
    plan = solve(instance)
    errors = verify(instance, plan)
    if errors:
        sys.exit("invalid plan: " + "; ".join(errors))
    return plan


def main() -> None:
    back = SweepInstance(broom=(5.485, -6.40))
    side = SweepInstance(broom=(-3.66, 11.0))
    cases = []
    for instance, where in ((back, "Broom on the back fence"), (side, "Broom on the side fence by the net")):
        plan = solved(instance)
        cases.append((
            instance, plan, where,
            f"{plan.objective:.1f} s = {instance.sweep_time:.1f} s sweeping + "
            f"{plan.carry_distance / instance.carry_speed:.1f} s carrying   ·   {len(plan.runs)} runs",
        ))
    OUTPUT.parent.mkdir(exist_ok=True)
    draw_linkedin(
        cases,
        str(OUTPUT),
        headline="Sweeping the lines of a clay court with a MILP model",
        subline="Every line exactly once, broom lifted between runs, back to its place"
                "   ·   minimise the total time (1 m/s sweeping and carrying)",
        footer="Solved to optimality with OR-Tools + SCIP",
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
