# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""Top view of one half of the court with a sweeping route (matplotlib)."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from line_sweeping.instance import SweepInstance
from line_sweeping.solution import MoveKind, SweepPlan

SURFACE = "#fcfcfb"
CLAY = "#f3e3d6"  # pale clay, so that the route colours stand out
CLAY_EDGE = "#d9c3b1"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8880"
LINE = "#ffffff"
NET = "#3d3a36"
CARRY = "#52514e"
# Runs are a sequence, so they share one hue, light (first) to dark (last).
# The two ends are interpolated in OKLab; up to 7 runs pass the ordinal checks
# on CLAY (monotone lightness, visible steps, light end >= 2:1).
RUN_FIRST = (0.6498, -0.0229, -0.1426)  # #5598e7 in OKLab
RUN_LAST = (0.3220, -0.0184, -0.0921)  # #0b2c58 in OKLab

RUNBACK = 6.40  # ITF recommended space behind the baseline [m]
SIDE_RUN = 3.66  # ITF recommended space beside the sidelines [m]
NET_POST = 0.914  # net posts stand this far outside the doubles sidelines [m]


def _oklab_to_hex(lab: tuple[float, float, float]) -> str:
    L, a, b = lab
    l, m, s = ((L + ka * a + kb * b) ** 3 for ka, kb in
               ((0.3963377774, 0.2158037573), (-0.1055613458, -0.0638541728), (-0.0894841775, -1.2914855480)))
    linear = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
              -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
              -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)

    def channel(c: float) -> int:
        c = min(max(c, 0.0), 1.0)
        return round(255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055))

    return "#" + "".join(f"{channel(c):02x}" for c in linear)


def run_colors(n: int) -> list[str]:
    """n colours of one hue from light (first run) to dark (last run)."""
    if n <= 1:
        return [_oklab_to_hex(RUN_FIRST)] * n
    return [_oklab_to_hex(tuple(f + (l - f) * k / (n - 1) for f, l in zip(RUN_FIRST, RUN_LAST))) for k in range(n)]


def draw_plan(ax: Axes, instance: SweepInstance, plan: SweepPlan, title: str = "", note: str = "") -> None:
    """Draw the half court seen from above, net at the top, with the route."""
    court = instance.court
    w, net = court.doubles_width, court.half_length
    bx, by = instance.broom

    margin = 1.0
    ax.set_xlim(min(-SIDE_RUN, bx) - margin, max(w + SIDE_RUN, bx) + margin)
    ax.set_ylim(min(-RUNBACK, by) - margin, max(net + 1.0, by) + margin)
    ax.set_aspect("equal")
    ax.axis("off")

    # Clay inside the fence, the painted lines and the net.
    ax.add_patch(Rectangle((-SIDE_RUN, -RUNBACK), w + 2 * SIDE_RUN, net + RUNBACK + 1.0,
                           facecolor=CLAY, edgecolor=CLAY_EDGE, linewidth=1.2, zorder=0))
    for line in instance.lines:
        ax.plot(*zip(line.start, line.end), color=LINE, linewidth=5, solid_capstyle="projecting", zorder=1)
    ax.plot([-NET_POST, w + NET_POST], [net, net], color=NET, linewidth=2.5, zorder=6)
    for x in (-NET_POST, w + NET_POST):
        ax.add_patch(Circle((x, net), 0.12, facecolor=NET, edgecolor="none", zorder=6))
    ax.text(w / 2, net + 0.35, "net", ha="center", va="bottom", fontsize=9, color=TEXT_MUTED)

    runs = plan.runs
    colors = run_colors(len(runs))
    for k, (run, color) in enumerate(zip(runs, colors), start=1):
        for move in run:
            ax.plot(*zip(move.start, move.end), color=color, linewidth=3, solid_capstyle="butt", zorder=3)
            mid = ((move.start[0] + move.end[0]) / 2, (move.start[1] + move.end[1]) / 2)
            if move.length > 0.5:
                ax.add_patch(FancyArrowPatch(move.start, mid, arrowstyle="-|>,head_length=0.5,head_width=0.3",
                                             mutation_scale=22,
                                             color=color, linewidth=0, shrinkA=0, shrinkB=0, zorder=4))
        sx, sy = run[0].start
        ax.add_patch(Circle((sx, sy), 0.42, facecolor=color, edgecolor=SURFACE, linewidth=1.5, zorder=8))
        ax.text(sx, sy, str(k), ha="center", va="center", fontsize=9, color="white", fontweight="bold",
                zorder=9)

    # Carries, drawn slightly curved so that they stay visible where they run along a line.
    for move in plan.carries:
        if move.length < 1e-9:
            continue
        ax.add_patch(FancyArrowPatch(move.start, move.end, connectionstyle="arc3,rad=0.12",
                                     arrowstyle="-|>", mutation_scale=11, color=CARRY, linewidth=1.2,
                                     linestyle=(0, (4, 3)), shrinkA=2, shrinkB=6, zorder=5))

    ax.plot([bx], [by], marker="s", markersize=10, color=TEXT, markeredgecolor=SURFACE, zorder=10)
    ax.text(bx + 0.45, by, "broom", ha="left", va="center", fontsize=9, color=TEXT_SECONDARY, zorder=10)

    if title:
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=TEXT, pad=22)
    if note:
        ax.text(0.0, 1.01, note, transform=ax.transAxes, ha="left", va="bottom", fontsize=10.5,
                color=TEXT_SECONDARY)


def _legend(fig: plt.Figure, y: float) -> None:
    handles = [
        Line2D([], [], color=run_colors(2)[0], linewidth=3, label="first run"),
        Line2D([], [], color=run_colors(2)[1], linewidth=3, label="last run (darker = later)"),
        Line2D([], [], color=CARRY, linewidth=1.2, linestyle=(0, (4, 3)), label="carrying the lifted broom"),
        Line2D([], [], color=TEXT, marker="s", linestyle="none", markersize=8, label="broom place"),
    ]
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(0.5, y), ncol=len(handles), frameon=False,
               fontsize=10, labelcolor=TEXT_SECONDARY, handlelength=2.2)


def plot_plan(instance: SweepInstance, plan: SweepPlan, title: str = "", note: str = "",
              width: float = 8.0) -> plt.Figure:
    """Figure with one plan and a legend, e.g. for a notebook. The figure is closed,
    so it is displayed once when returned from a notebook cell."""
    fig = plt.figure(figsize=(width, width * 1.12), dpi=110, facecolor=SURFACE)
    ax = fig.add_axes((0.03, 0.08, 0.94, 0.84))
    ax.set_facecolor(SURFACE)
    draw_plan(ax, instance, plan, title, note)
    _legend(fig, 0.035)
    plt.close(fig)
    return fig


def draw_linkedin(
    cases: list[tuple[SweepInstance, SweepPlan, str, str]],
    path: str,
    headline: str,
    subline: str,
    footer: str,
) -> None:
    """Draw several plans side by side into one 16:9 image."""
    fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=SURFACE)
    fig.text(0.04, 0.925, headline, fontsize=26, fontweight="bold", color=TEXT, va="bottom")
    fig.text(0.04, 0.885, subline, fontsize=14, color=TEXT_SECONDARY, va="bottom")

    left, right, gap = 0.04, 0.96, 0.04
    width = (right - left - gap * (len(cases) - 1)) / len(cases)
    for k, (instance, plan, title, note) in enumerate(cases):
        ax = fig.add_axes((left + k * (width + gap), 0.1, width, 0.72))
        ax.set_facecolor(SURFACE)
        draw_plan(ax, instance, plan, title, note)

    _legend(fig, 0.05)
    fig.text(0.96, 0.015, footer, fontsize=11, color=TEXT_MUTED, ha="right", va="bottom")
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
