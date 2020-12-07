Lesson 11 Tasks: Speculative AOT Optimization
=============================================

An implementation of ``Speculative Optimization'' from 6120 lesson 11.
The program, `specop.py` expects a bril program on standard in and the
filename of a profile produced by the associated brili extension.

The tracer starts tracing at the beginning of main and stops at the first
instruction it recognizes has already been run (i.e., the first backedge).

The most limiting choice about my implementation is that if the trace finds that
the code performs a side-effect (such as printing), we bail out and emit code to
just recover to unoptimized code. In addtion, my choice of when to trace means
that we can only really straight-line the *first* time through a loop. That is,
the "optimizer" essentially unrolls one loop iteration and runs it "faster". So
in essence, the optimizer does almost nothing to actually optimize.

Lesson 3's LVN/DCE passes are run on the "speculatively-optimized" programs.

Running the program
-------------------

This program works only with the associated brili extension, here:
https://github.com/mdmoeller/bril/tree/tracer

To run `specop.py`, one first starts by getting a profile using the brili
extension, -t:

$ bril2json ./bench/collatz.bril | brili -t 7

This will generate a `profile.txt`. Then we run the following pipeline (note
that specop.py opens `profile.txt`.

$ bril2json ./bench/collatz.bril | python3 specop.py | python3 ../03/lvn.py | python3 ../03/dce.py | brili -p 7


Testing and performance
-----------------------
I tested the "optimization" on the bril benchmark suite using brench. To do
this, I combined the above two pipelines into a single brench pipeline. The
results are in `brench-results.csv`. Sadly, I believe the pipeline has a race
condition, causing varying results. At this point, I am confident there is a bug
in dce.py causing `pythagorean_triple` to fail; `mat-mal` fails consistently but
I do not know why, and all of the others work at least some of the time.

Note in particular the brench target `lvndce`: this is the lesson 03 LVN/DCE
code running as a baseline. It is clear from this baseline that most of
improvement in the specop examples is due to the LVN/DCE only.


"Future Work"
--------------

If I had had more time, I would've wanted to spend a lot more time experimenting
with when to start and stop the trace. Refining where to stop the trace is
particularly difficult because you need a way to insert code to jump to the
corresponding place of non-"optimized".
