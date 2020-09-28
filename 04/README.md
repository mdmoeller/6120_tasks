Mark Moeller - Lesson 4: Dataflow analysis
==========================================

A python implementation of constant propagation is provided in conprop.py.

The program computes the set of variables at each point in the CFG that must
contain an int constant, and, for each such variable, its constant value.

Note: I only handled propagation/folding of int constants; bools are ignored.

The code also contains functions for defined-variables (the trivial
analysis), which shows the modularity of the worklist function.

The code for form_blocks is from the beginning of the course. The format of the
output comes from Adrian's example for this Task. Everything else is mine. 




Testing
-------

I have created a set of ``toy examples'' meant to demonstrate the features of
the program in ./examples. I also ran the program on a number of the
bril/benchmarks and inspected the results manually. Two examples of this
are provided in the files ./examples/{collatz,euclid}.out, which are from the
so-named bril/benchmarks.

For this purpose, I found the following useful:

$ prog=bench/*.bril; clear; echo $prog; cat $prog; bj $prog | ./conprop.py

I did not use brench or turnt, as the format of [even the correct] results was
changing frequently as I changed the programs.
