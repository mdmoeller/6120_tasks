#!/usr/bin/python3
import sys
from brilpy import *

PROFILE = 'profile.txt'

def main():

    prog = json.load(sys.stdin)

    # Hack to make brench work: we wait to open 'profile.txt' until *after*
    # we've finished reading from stdin
    trace = json.load(open(PROFILE))

    mainfunc = list(filter(lambda x: x['name'] == 'main', prog['functions']))[0]
    
    instrs = mainfunc["instrs"]
    t_instrs = trace["instrs"]

    mainfunc["instrs"] = t_instrs + [{"label":"recover"}] + instrs

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
