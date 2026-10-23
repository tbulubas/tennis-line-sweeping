# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""Input data of a line sweeping instance (metres, seconds)."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from line_sweeping.court import CourtDimensions, Line, LineGraph, Point, build_graph, half_court_lines


@dataclass(frozen=True)
class SweepInstance:
    """Parameters of the problem statement.

    Attributes:
        broom: B, place where the broom is kept, in court coordinates [m].
        sweep_speed: v_s, walking speed while sweeping a line [m/s].
        carry_speed: v_c, walking speed while carrying the lifted broom [m/s].
        court: court dimensions (ITF standard by default).
        separate_centre_mark: sweep the centre mark as a line of its own instead
            of together with the baseline.
    """

    broom: Point
    sweep_speed: float = 1.0
    carry_speed: float = 1.0
    court: CourtDimensions = field(default_factory=CourtDimensions)
    separate_centre_mark: bool = False

    def __post_init__(self) -> None:
        if self.sweep_speed <= 0 or self.carry_speed <= 0:
            raise ValueError("speeds must be positive")
        if not self.graph.is_connected():
            raise ValueError("the lines must form one connected network")

    @cached_property
    def lines(self) -> list[Line]:
        """The lines to sweep: all lines of one half of the court."""
        return half_court_lines(self.court, self.separate_centre_mark)

    @cached_property
    def graph(self) -> LineGraph:
        return build_graph(self.lines)

    @property
    def sweep_length(self) -> float:
        """Total length of all lines; each is swept exactly once."""
        return sum(line.length for line in self.lines)

    @property
    def sweep_time(self) -> float:
        """Time spent sweeping; the same for every plan."""
        return self.sweep_length / self.sweep_speed

    @property
    def min_runs(self) -> int:
        """Lower bound on the number of sweeping runs: half the number of odd vertices."""
        return max(1, len(self.graph.odd_vertices) // 2)
