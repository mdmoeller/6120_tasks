# llvm-pass-block-profiler

An LLVM pass based on Adrian Sampson's skeleton LLVM pass 
(https://github.com/sampsyo/llvm-pass-skeleton.git).

The pass adds instrumentation to count dynamic executions of each block, in each
function of a file. These counts are printed to stdout as soon as the program
exits.

I have included a program I wrote some years ago with functions to play
2048 (https://play2048.co) using various strategies, which is used in the example
below. (sadly the program depends on ncurses). I have also included a file,
ex/out.txt, the output of the example.

Build the pass:

    $ cd llvm-pass-block-profiler
    $ mkdir build
    $ cd build
    $ cmake ..
    $ make
    $ cd ..

Build the block execution counting module:

    $ cd instrumenter
    $ gcc -c count.c
    $ cd ..

Instrument some code:

    $ cd ./ex
    $ clang -Xclang -load -Xclang ../build/instrumenter/libInstrumPass.so -c tfe.c
    $ clang ../instrumenter/count.o tfe.o -o tfe -lcurses

Try it out!:

    $ ./tfe -e
