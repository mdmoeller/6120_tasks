#!/usr/bin/python3

import sys
import json
from brilpy import *
from functools import reduce
from ssa import from_ssa


def main():
    prog = json.load(sys.stdin)
    json.dump(from_ssa(prog), sys.stdout)


if __name__ == '__main__':
    main()
