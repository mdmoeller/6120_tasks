#!/usr/bin/python3
import sys
import json

from ssa import to_ssa

def main():
    prog = json.load(sys.stdin)
    json.dump(to_ssa(prog), sys.stdout)


if __name__ == '__main__':
    main()
