# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

"""Geometry of one half of a tennis court and the graph of its lines (metres).

Coordinates: the origin is the left end of the baseline as seen by a player
standing behind the baseline and facing the net; x runs along the baseline to
the right, y towards the net. The net is at y = length / 2.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

Point = tuple[float, float]

TOLERANCE = 1e-9


@dataclass(frozen=True)
class CourtDimensions:
    """Dimensions of a tennis court, ITF Rules of Tennis, Rule 1 (defaults).

    All measurements are to the outside of the lines. Line widths are
    neglected in iteration 1, so a line is a segment of zero width.

    Attributes:
        length: full length of the court, baseline to baseline (23.77 m).
        doubles_width: width between the doubles sidelines (10.97 m).
        singles_width: width between the singles sidelines (8.23 m).
        service_line_distance: distance of the service line from the net (6.40 m).
        centre_mark_length: length of the centre mark on the baseline (0.10 m).
    """

    length: float = 23.77
    doubles_width: float = 10.97
    singles_width: float = 8.23
    service_line_distance: float = 6.40
    centre_mark_length: float = 0.10

    def __post_init__(self) -> None:
        if min(self.length, self.doubles_width, self.singles_width) <= 0:
            raise ValueError("court length and widths must be positive")
        if self.singles_width > self.doubles_width:
            raise ValueError("singles_width must not exceed doubles_width")
        if not 0 < self.service_line_distance < self.half_length:
            raise ValueError("the service line must lie between the baseline and the net")
        if not 0 <= self.centre_mark_length < self.half_length - self.service_line_distance:
            raise ValueError("the centre mark must be shorter than the distance to the service line")

    @property
    def half_length(self) -> float:
        """Distance from the baseline to the net."""
        return self.length / 2

    @property
    def alley_width(self) -> float:
        """Distance between a doubles and the neighbouring singles sideline."""
        return (self.doubles_width - self.singles_width) / 2

    @property
    def service_line_y(self) -> float:
        """Distance of the service line from the baseline."""
        return self.half_length - self.service_line_distance


@dataclass(frozen=True)
class Line:
    """A painted line (tape) of the court, given by its two end points."""

    name: str
    start: Point
    end: Point

    @property
    def length(self) -> float:
        return distance(self.start, self.end)


def distance(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def half_court_lines(court: CourtDimensions, separate_centre_mark: bool = False) -> list[Line]:
    """All lines on one player's half of the court, doubles lines included.

    The centre mark is swept together with the baseline (the broom is wider
    than the 10 cm mark), so by default it is no line of its own and the
    baseline is not split at it. With separate_centre_mark it is a line.
    """
    w, net = court.doubles_width, court.half_length
    a, s, c = court.alley_width, court.service_line_y, court.doubles_width / 2
    lines = [
        Line("baseline", (0.0, 0.0), (w, 0.0)),
        Line("left doubles sideline", (0.0, 0.0), (0.0, net)),
        Line("right doubles sideline", (w, 0.0), (w, net)),
    ]
    if a > TOLERANCE:  # without alleys the singles sidelines are the doubles sidelines
        lines += [
            Line("left singles sideline", (a, 0.0), (a, net)),
            Line("right singles sideline", (w - a, 0.0), (w - a, net)),
        ]
    lines += [
        Line("service line", (a, s), (w - a, s)),
        Line("centre service line", (c, s), (c, net)),
    ]
    if separate_centre_mark and court.centre_mark_length > TOLERANCE:
        lines.append(Line("centre mark", (c, 0.0), (c, court.centre_mark_length)))
    return lines


def _on_segment(p: Point, line: Line, tol: float = TOLERANCE) -> float | None:
    """Parameter t ∈ [0, 1] of p on the line, or None if p is not on it."""
    (x1, y1), (x2, y2) = line.start, line.end
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    t = ((p[0] - x1) * dx + (p[1] - y1) * dy) / length_sq
    if not -tol <= t <= 1 + tol:
        return None
    closest = (x1 + t * dx, y1 + t * dy)
    return min(max(t, 0.0), 1.0) if distance(p, closest) <= tol * max(1.0, math.sqrt(length_sq)) else None


def _crossing(first: Line, second: Line) -> Point | None:
    """Intersection point of two non-parallel lines, if they meet."""
    (x1, y1), (x2, y2) = first.start, first.end
    (x3, y3), (x4, y4) = second.start, second.end
    denominator = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(denominator) <= TOLERANCE:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / denominator
    p = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return p if _on_segment(p, first) is not None and _on_segment(p, second) is not None else None


def stop_points(lines: list[Line]) -> list[Point]:
    """Points where sweeping may start or stop: line ends, corners and junctions."""
    points: list[Point] = []

    def add(p: Point) -> None:
        if all(distance(p, q) > 1e-6 for q in points):
            points.append(p)

    for line in lines:
        add(line.start)
        add(line.end)
    for k, first in enumerate(lines):
        for second in lines[k + 1:]:
            p = _crossing(first, second)
            if p is not None:
                add(p)
    return points


@dataclass(frozen=True)
class Vertex:
    """A stop point of the line graph."""

    point: Point
    lines: tuple[str, ...]
    degree: int

    @property
    def kind(self) -> str:
        if self.degree == 1:
            return "line end"
        return "corner" if self.degree == 2 else "junction"

    @property
    def label(self) -> str:
        return " × ".join(self.lines) if len(self.lines) > 1 else f"end of {self.lines[0]}"


@dataclass(frozen=True)
class Segment:
    """A piece of a line between two neighbouring stop points (an edge of the graph)."""

    u: int
    v: int
    line: str
    length: float


@dataclass(frozen=True)
class LineGraph:
    """Undirected graph of the lines: vertices are stop points, edges are segments."""

    vertices: tuple[Vertex, ...]
    segments: tuple[Segment, ...]

    @property
    def total_length(self) -> float:
        return sum(s.length for s in self.segments)

    @property
    def odd_vertices(self) -> list[int]:
        return [k for k, v in enumerate(self.vertices) if v.degree % 2 == 1]

    def is_connected(self) -> bool:
        if not self.vertices:
            return False
        neighbours: dict[int, set[int]] = defaultdict(set)
        for s in self.segments:
            neighbours[s.u].add(s.v)
            neighbours[s.v].add(s.u)
        seen, stack = {0}, [0]
        while stack:
            for nxt in neighbours[stack.pop()] - seen:
                seen.add(nxt)
                stack.append(nxt)
        return len(seen) == len(self.vertices)


def build_graph(lines: list[Line]) -> LineGraph:
    """Split every line at the stop points lying on it."""
    points = stop_points(lines)
    on_lines: dict[int, list[str]] = defaultdict(list)
    degree: dict[int, int] = defaultdict(int)
    segments: list[Segment] = []
    for line in lines:
        on_line = sorted((t, k) for k, p in enumerate(points) if (t := _on_segment(p, line)) is not None)
        for _, k in on_line:
            on_lines[k].append(line.name)
        for (_, a), (_, b) in zip(on_line, on_line[1:]):
            segments.append(Segment(a, b, line.name, distance(points[a], points[b])))
            degree[a] += 1
            degree[b] += 1
    vertices = tuple(Vertex(p, tuple(on_lines[k]), degree[k]) for k, p in enumerate(points))
    return LineGraph(vertices, tuple(segments))
