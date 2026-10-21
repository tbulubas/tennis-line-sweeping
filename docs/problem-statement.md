# Sweeping the Lines of a Clay Tennis Court — Problem Statement

## Context

On a clay court the lines are tapes laid into the clay. After play they are
covered with clay and have to be swept clean with a line broom. The broom is
usually kept somewhere by the fence. The goal is to plan the route of the
person sweeping so that all lines are clean as quickly as possible.

The problem is to be solved with a Mixed-Integer Linear Programming (MILP)
model.

## Geometry

The court has the standard dimensions of the ITF *Rules of Tennis* (Rule 1).
All measurements are to the outside of the lines.

| Quantity                               | Value    |
|----------------------------------------|----------|
| court length (baseline to baseline)    | 23.77 m  |
| half court (baseline to net)           | 11.885 m |
| doubles width                          | 10.97 m  |
| singles width                          | 8.23 m   |
| alley (doubles to singles sideline)    | 1.37 m   |
| service line, distance from the net    | 6.40 m   |
| service line, distance from the baseline | 5.485 m |
| centre mark on the baseline            | 0.10 m long |
| net posts, outside the doubles sidelines | 0.914 m |
| recommended space behind the baseline  | 6.40 m   |
| recommended space beside the sidelines | 3.66 m   |

Only **one half** of the court is swept — the side of one player — with
**all** its lines, the doubles lines included:

```
          net  ─────────────────────────────────────────────
   N0 ●───N1 ●───────────────── NC ●──────────────── N2 ●───● N3
      │      │                     │                   │      │
      │      │                     │ centre service    │      │
      │      │                     │ line              │      │
      │   S1 ●─────────────────── SC ●────────────── S2 ●      │
      │      │        service line                     │      │
      │      │                                         │      │
      │      │ left singles               right singles│      │
      │      │ sideline                        sideline│      │
   B0 ●───B1 ●───────────────── BC ●──────────────── B2 ●───● B3
                                   ╹ centre mark (ends at CM)
   ^ left doubles sideline       baseline       right doubles sideline ^
```

| Line                     | From → to                       | Length   |
|--------------------------|---------------------------------|----------|
| baseline                 | B0 → B3                         | 10.97 m  |
| left / right doubles sideline | baseline → net             | 2 × 11.885 m |
| left / right singles sideline | baseline → net             | 2 × 11.885 m |
| service line             | S1 → S2                         | 8.23 m   |
| centre service line      | SC → net                        | 6.40 m   |
| centre mark              | BC → CM, into the court         | 0.10 m   |
| **total**                |                                 | **73.24 m** |

Coordinates: the origin is the left end of the baseline (B0) as seen by the
player behind the baseline facing the net; x runs along the baseline to the
right, y towards the net. The net is at y = 11.885 m.

## The broom

- The broom is kept at a place **B** = (x_B, y_B), given in court coordinates.
  Usually this is somewhere by the fence.
- The broom is either **down** (sweeping) or **lifted** (being carried).

## Rules

1. The work **starts at B by picking up the broom** and **ends by putting the
   broom back at B**.
2. The broom is carried from B to a corner, a junction of lines or the end of
   a line, and sweeping starts there.
3. A **sweeping run** follows the lines without lifting the broom. It may turn
   onto another line at a corner or a junction.
4. **Every part of every line is swept exactly once.**
5. When a run cannot or should not continue, the broom is lifted, carried to
   another corner, junction or line end, and the next run starts there.
6. While the broom is lifted it is carried in a straight line, across the
   court or along lines already swept.

## Inputs

| Symbol | Meaning                                    | Unit | Default |
|--------|--------------------------------------------|------|---------|
| x_B, y_B | place of the broom, in court coordinates | m    | —       |
| v_s    | walking speed while sweeping               | m/s  | 1.0     |
| v_c    | walking speed while carrying the broom     | m/s  | 1.0     |
|        | court dimensions                           | m    | ITF     |

In iteration 1 both speeds are equal (v_s = v_c).

## Decisions

- The number of sweeping runs.
- For each run: where it starts, which line pieces it sweeps in which
  direction and order, and where it ends.
- The order of the runs, i.e. where the broom is carried in between.

## Objective

**Minimise the total time** from picking up the broom to putting it back:

```
time = (length swept) / v_s + (length carried) / v_c
```

Observation: every line is swept exactly once, so the sweeping time
73.24 m / v_s is the same for every plan. What the plan decides is the
carrying: how often and how far the broom has to be carried. In iteration 1
the speeds therefore only change the reported time, not the best route.

A lower bound on the number of runs: a run passes through a junction with an
even number of line pieces, but at a vertex where an **odd** number of line
pieces meet, at least one run has to start or end. The half court has 12
such vertices (the six junctions B1, BC, B2, S1, SC, S2 and the six line ends
N0, N1, NC, N2, N3, CM), so every plan has **at least 6 runs**.

## Modelling assumptions

1. **Line width is neglected** in iteration 1: a line is a segment of zero
   width at its nominal position, and the broom covers the line's width in
   one pass.
2. **Where runs start and end.** Runs start and end only at the *stop points*:
   corners (B0, B3), junctions (B1, BC, B2, S1, SC, S2) and line ends (N0, N1,
   NC, N2, N3, CM). The ends at the net count as line ends: a line that ends
   there can only be left by lifting the broom.
3. **Carrying is straight-line.** The broom is carried along the straight
   segment between two points; the court has no obstacles apart from the net,
   and a walk along the net (e.g. from N0 to N1) is taken as straight, just in
   front of it.
4. **No time for lifting and setting down the broom** and none for turning at
   a corner.
5. Sweeping direction does not matter.

## Planned iterations

| Iteration | Change |
|-----------|--------|
| 1         | Equal speeds v_s = v_c; assumptions above (this spec) |
| later     | to be decided, e.g. different speeds, a time for every lift, direction-dependent sweeping, line widths, several workers or several courts |

---

© 2026 Taras Bulubas. All rights reserved. See [LICENSE](../LICENSE).
