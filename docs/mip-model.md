# Sweeping the Lines — MILP Model (Iteration 1)

Mixed-integer model for the line sweeping problem described in
[`problem-statement.md`](problem-statement.md).

## Idea

Draw the lines as a graph: the stop points (corners, junctions, line ends)
are the **vertices**, the pieces of line between neighbouring stop points are
the **segments**. Add one more node, the broom place **B**.

The route of the worker is a closed walk that starts and ends at B. Every
segment is walked exactly once *with the broom down*; in between, the worker
walks straight from one node to another *with the broom lifted*. Seen as a
directed multigraph — one arc per swept segment in the chosen direction, one
arc per carry — the route uses every arc exactly once: it is an **Euler
circuit**.

A directed multigraph has an Euler circuit exactly when it is connected and
every node is left as often as it is reached. The lines of a half court are
connected, and B is joined to them by its carries, so the model only has to
choose

1. a **direction** for every segment (binary), and
2. a set of **carries** between nodes (binary),

such that every node is **balanced**. The Euler circuit itself — the order of
the moves — is constructed afterwards (Hierholzer's algorithm).

## Indices and sets

| Symbol                 | Meaning                                                      |
|------------------------|--------------------------------------------------------------|
| v ∈ V                  | vertices: stop points on the lines (12 on a half court)      |
| B                      | the broom place                                              |
| N = V ∪ {B}            | nodes                                                        |
| e ∈ E                  | segments; e = {u(e), v(e)}, listed with an arbitrary orientation u(e) → v(e) (12 on a half court) |
| (a, b) ∈ A             | carries: ordered pairs of distinct nodes a, b ∈ N            |
| deg(v)                 | number of segments at vertex v                               |
| O ⊆ V                  | vertices of odd degree (10 on a half court)                  |

## Parameters

| Symbol  | Meaning                                         | Unit |
|---------|-------------------------------------------------|------|
| ℓ(e)    | length of segment e                             | m    |
| c(a, b) | straight-line distance between nodes a and b    | m    |
| v_s     | speed while sweeping                            | m/s  |
| v_c     | speed while carrying                            | m/s  |

## Decision variables

| Variable          | Domain | Meaning                                                    |
|-------------------|--------|------------------------------------------------------------|
| s(e), e ∈ E       | {0, 1} | 1: e is swept from u(e) to v(e); 0: from v(e) to u(e)       |
| w(a,b), (a,b) ∈ A | {0, 1} | 1: the broom is carried straight from a to b once          |

Derived expressions — sweeps leaving and reaching vertex v:

    S⁺(v) = Σ_{e: u(e)=v} s(e) + Σ_{e: v(e)=v} (1 − s(e))
    S⁻(v) = Σ_{e: v(e)=v} s(e) + Σ_{e: u(e)=v} (1 − s(e))  = deg(v) − S⁺(v)

and carries leaving and reaching node a:

    C⁺(a) = Σ_{b ≠ a} w(a,b),        C⁻(a) = Σ_{b ≠ a} w(b,a)

## Constraints

Balance — every vertex is left as often as it is reached:

    (1)  S⁺(v) + C⁺(v) = S⁻(v) + C⁻(v)                      ∀ v ∈ V

The broom is picked up once and put back once:

    (2)  C⁺(B) = 1,   C⁻(B) = 1

At a vertex of odd degree the sweeps alone cannot be balanced, so a run has
to start or end there (valid inequality, implied by (1) for integer s, but
much stronger in the LP relaxation):

    (3)  C⁺(v) + C⁻(v) ≥ 1                                   ∀ v ∈ O

Carrying the broom from a to b and later from b back to a never pays off:
dropping both carries keeps every vertex balanced and saves 2·c(a, b):

    (4)  w(a,b) + w(b,a) ≤ 1                                 ∀ a, b ∈ V, a < b

Connectivity needs no constraint: the segments connect all vertices (the
instance checks this), and (2) connects B to them.

## Objective

Minimise the total time, sweeping plus carrying:

    min  Σ_{e ∈ E} ℓ(e) / v_s  +  Σ_{(a,b) ∈ A} c(a,b) / v_c · w(a,b)

The first term is a constant: every segment is swept exactly once.

## Why binary carries suffice

A carry could in principle be needed twice between the same two vertices.
Dropping both copies changes the balance of a and b by two each, but the
segments and the remaining carries still form a connected graph in which
every vertex has even degree. Such a graph has an (undirected) Euler circuit;
orienting the segments along it gives a new s that balances every vertex
again — at a lower cost. So an optimal plan never carries the broom twice
between the same pair of vertices, and w can be binary.

## From the solution to the route

1. Build the directed multigraph of the sweep arcs (direction from s) and
   the carry arcs (w = 1).
2. Hierholzer's algorithm finds an Euler circuit starting at B. At every node
   it continues with a sweep arc if one is left, so the runs stay long.
3. Consecutive carries a → b → c are merged into one carry a → c when b lies
   on the straight segment between a and c (no extra cost).

The result is the sequence of moves: carry, run 1, carry, run 2, …, carry
back to B. `verify` checks this route independently, using only positions
and the painted lines.

## Model size (half court)

| Item               | Count                | with a separate centre mark |
|--------------------|----------------------|-----------------------------|
| binaries s         | \|E\| = 12           | 14                          |
| binaries w         | \|N\|·(\|N\|−1) = 13·12 = 156 | 15·14 = 210        |
| constraints (1)    | \|V\| = 12           | 14                          |
| constraints (2)    | 2                    | 2                           |
| constraints (3)    | \|O\| = 10           | 12                          |
| constraints (4)    | \|V\|·(\|V\|−1)/2 = 66 | 91                        |

SCIP solves it to optimality in a fraction of a second.

## Independent check of optimality

With straight-line distances the optimum can also be computed without the
MILP: B is joined to two vertices u and v (possibly u = v), and the other
carries pair up the remaining vertices of odd degree — a minimum perfect
matching on O, with u and v toggled in or out of O. The tests compute this by
dynamic programming over all subsets and compare it with the MILP optimum.
The MILP is kept because it extends to the later iterations (direction- or
time-dependent costs, lifting times, several workers), where this shortcut no
longer holds.

## Examples

All with the ITF half court and v_s = v_c = 1 m/s; the centre mark is swept
with the baseline, so sweeping takes 73.14 s.

**Broom on the back fence, behind the centre mark, B = (5.485, −6.40).**
5 runs, carrying 29.68 m, total **102.82 s**. The broom is carried 7.61 m
to B1, the first run sweeps the left corner and the left doubles sideline up
to the net, the second sweeps the left singles sideline down and the baseline
from B1 to the right corner in one go, and the last run ends at B2, again
7.61 m from B.

**Broom on the side fence next to the net, B = (−3.66, 11.00).**
5 runs, carrying 27.61 m, total **100.75 s**. The first run starts at N0,
the line end nearest B (3.77 m), and sweeps the left doubles sideline, the
whole baseline and the right doubles sideline; the last run ends at N1,
5.11 m from B.

Both reach the lower bound of 5 runs.

**With the centre mark as a line of its own** (back fence again): 6 runs,
carrying 29.78 m, total **103.02 s**. The 10 cm mark costs one more run and
0.20 s — 0.10 m of sweeping and 0.10 m of carrying to its tip.

## Outlook — later iterations

- **Different speeds** (v_s ≠ v_c): only the weights change; the route stays
  the same in iteration 1, since the sweeping time is constant.
- **Time to lift and set down the broom**: add t_lift · Σ w(a,b) to the
  objective; fewer, longer runs become more valuable.
- **Direction-dependent sweeping** (e.g. towards the fence): give the two
  directions of a segment different times, ℓ(e)/v_s⁺ · s(e) + ℓ(e)/v_s⁻ ·
  (1 − s(e)).
- **Several workers or several courts**: one copy of the variables per
  worker, every segment assigned to one worker; the connectivity argument
  then needs explicit constraints.

---

© 2026 Taras Bulubas. All rights reserved. See [LICENSE](../LICENSE).
