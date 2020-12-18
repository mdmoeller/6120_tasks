#!/bin/bash

cbril > a.ll
clang a.ll
./a.out "$@"
rm a.ll a.out
