Mark Moeller - Lesson 3: DCE and LVN
====================================

Python implementations of trivial Dead Code Elimation (both global and local)
and Local Value Numbering are provided in dce.py and lvn.py respectively.

Both files expect a bril program in JSON from stdin and write another bril
program with the same behavior to stdout.




Brench Testing
--------------

I have created a set of ``toy examples'' meant to demonstrate the features of
the dce and lvn programs in .benchmarks/. They can be run with:

$ brench ./toy_examples.toml


I also have verified that neither program affects the correct behavior of the
bril repository benchmark suite. This can be checked using bril-bench.toml,
although one would need to update the location of their own bril
repository/benchmark suite.

A csv file, dce_lvn.csv with both benchmarks shows the optimizations'
improvements, which was created with the following:

$ brench toy_examples.toml > dce_lvn.csv && brench bril-bench.toml >> dce_lvn.csv
