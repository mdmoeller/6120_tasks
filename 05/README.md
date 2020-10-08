Mark Moeller - Lesson 5: SSA Conversion
=======================================

Two programs are provided that convert bril programs to and from ssa,
`to_ssa.py` and `from_ssa.py`.

I also consolidated general CFG code in ../brilpy.py.



Testing
-------

Sadly, I suspect that bugs still exist.

My ssa conversions were tested on the bril benchmark suite:
13/21 pass their turnt test in ssa and back out again
14/21 pass `is_ssa.py`

I have not yet investigated the cause for failures of the other 8/21 benchmarks,
but a few would be due to use of features I chose not to support.
