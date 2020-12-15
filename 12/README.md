Lesson 12 Tasks: Synthesis
==========================

To extend the examples in minisynth, have created a synthesizer that
automatically builds a framework for variable-holes. A variable-hole in a sketch
is one that must be filled with *any* of the variables in the specification
program.

For example,
If we have spec:
8 * x + 16 * y

and sketch:
v1 << h1 + v2 << h2

Then
v1= x, h1= 3, v2= y, h2= 4

produces a correct program.

Difficulty
----------

This was definitely more difficult a task than I expected. (I was thinking this
would be my warm-up exercise). I chose to implement the "variable-switch" that
would need to be generated for each v-variable by nesting ternary operators,
and creating a z3 expression to set the variable equal to the ternary chain.

To make the goal, we want to satisfy an implication:
the conjunction of the v-variable equalites implies the equivalence of the
programs.

In otherwords for the above example, we would run z3 on:

\forall x, y, v1, v2: (v1 = (c0? x : y) ^ v2 = (c1: x : y)) => (8 * x + 16 * y) == (v1 << h1 + v2 << h2)

to find the above assignments to v1, v2, h1, and h2.

This solution feels much more complicated than it needs to be, but a better
approach (that remains general) escapes me.

Running the program
-------------------

The synthesizer works very similarly to the examples in minisynth. On stdin:
* The first line is a program to serve as specification
* The second line is a program sketch. Variables that start with h will be
  filled by constants, and variables that start with v will be filled with
  *some* program variable from the spec.

Examples
--------
I have included 6 examples that demonstrate the synthesizer well:

```
$ for i in `seq 0 6`; do printf "\n\nex$i:\n"; cat ex$i; printf "\n"; python3 ./synth.py < ex$i; done

ex0:
8 * x + 16 * y
v1 << h1 + v2 << h2

v1 == (c0? y : x)
v2 == (c1? y : x)
Success! [h2 = 3, h1 = 4, c1 = 0, c0 = 255]
(8 * x) + (16 * y)
(v1 << 4) + (v2 << 3)


ex1:
2 * x + y
2 * v1 + v2

v1 == (c0? y : x)
v2 == (c1? y : x)
Success! [c1 = 255, c0 = 0]
(2 * x) + y
(2 * v1) + v2


ex2:
2 * x * y 
x * v1 + y * v2

v1 == (c0? y : x)
v2 == (c1? y : x)
Success! [c1 = 0, c0 = 255]
(2 * x) * y
(x * v1) + (y * v2)


ex3:
x * z + z * y + x * z * y 
v1 * v2 + v2 * v3 + v1 * v2 * v3

v1 == (c0? y : (c1? z : x))
v2 == (c2? y : (c3? z : x))
v3 == (c4? y : (c5? z : x))
Success! [c5 = 0, c4 = 0, c3 = 255, c2 = 0, c1 = 255, c0 = 255]
((x * z) + (z * y)) + ((x * z) * y)
((v1 * v2) + (v2 * v3)) + ((v1 * v2) * v3)


ex4:
4 * x * y + x * x + 3 * z
(v1 * v2) << h + v2 * v2 + 3 * v3

v1 == (c0? z : (c1? y : x))
v2 == (c2? z : (c3? y : x))
v3 == (c4? z : (c5? y : x))
Success! [h = 2,
 c5 = 255,
 c4 = 255,
 c3 = 0,
 c2 = 0,
 c1 = 255,
 c0 = 0]
(((4 * x) * y) + (x * x)) + (3 * z)
(((v1 * v2) << 2) + (v2 * v2)) + (3 * v3)


ex5:
x * y * z + w * x * x + w * y + z * z * y
v2 * v2 * v3 + v4 * v1 * v2 + v1 * v4 * v1 + v4 * v3

v2 == (c0? w : (c1? z : (c2? y : x)))
v3 == (c3? w : (c4? z : (c5? y : x)))
v4 == (c6? w : (c7? z : (c8? y : x)))
v1 == (c9? w : (c10? z : (c11? y : x)))
Success! [c11 = 255,
 c10 = 255,
 c9 = 0,
 c8 = 255,
 c7 = 0,
 c6 = 0,
 c5 = 255,
 c4 = 255,
 c3 = 255,
 c2 = 0,
 c1 = 0,
 c0 = 0]
((((x * y) * z) + ((w * x) * x)) + (w * y)) + ((z * z) * y)
((((v2 * v2) * v3) + ((v4 * v1) * v2)) + ((v1 * v4) * v1)) + (v4 * v3)
```
