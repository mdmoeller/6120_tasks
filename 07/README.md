Lesson 7 Tasks: Loop Invariant Code Motion (LICM)
=================================================

An implementation of Loop Invariant Code Motion from 6120 lesson 7 (and lesson
5).  The program, `licm.py` expects a bril program *in ssa* on standard in, and
emits a program with loop invariant code motion performed if any opportunities
are identified.

The particular natural loops identified by this implementation might be unusual:
we first find all the back-edges, say `B->A` where A dominates B. For each of
these, we find a starting cycle by taking the intersection of the blocks
dominated by A and those that dominate B. Now it may be that other back-edges go
to A from other nodes. To simplify our construction we combine these other
cycles into one strongly connected component with header A. Indeed, anything
which is invariant in the separate cycles must still be invariant in this
combined view, due to the SSA restriction and the fact that the loops share
header A (in other words, for some node C such that `C->A` is a back-edge,
cannot vary with B unless B dominates C anyway).

The advantage to this view of combined natural loops is that each natural loop
will have only one header, which simplifies the modification of the phi nodes
after adding a preheader node. Any label in a phi that was outside the loop must
now come in through the preheader, so we simply adjust the phi's label
accordingly.

The program does not "relax the third criterion" of the 6120 lesson notes for
lesson 05. That is, code will only be moved outside of a loop from blocks that
happen to dominate all loop exits.


Testing and performance
-----------------------
I tested the "optimization" on the bril benchmark suite using brench. The
results are in `brench-results.csv`. The results give a modest improvement
compared to the ssa form of `sum-sq-diff`, `quadratic`, `check-primes`, and
`pythagorean_triple`. This is intuitive given the nature of the optimization,
since the more numerical benchmarks from the suite. In no case was there an
improvement over the pre-SSA form of the benchmark.  So the lesson is: this form
of loop invariant code motion by itself is not enough to pay for the overhead of
SSA.

The results of `brench-results.csv` are in tabular form in `brench-results.tab`
