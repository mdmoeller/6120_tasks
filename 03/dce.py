#!/usr/bin/python3


import json
import sys


TERM = 'jmp', 'br', 'ret'

def form_blocks(body):
    cur_block = []

    for inst in body:
        if 'op' in inst:
            cur_block.append(inst)

            # check for term
            if inst['op'] in TERM:
                yield cur_block
                cur_block = []

        else: # label
            if cur_block:
                yield cur_block

            cur_block = [inst]

    yield cur_block

def dce():
    prog = json.load(sys.stdin)


    # Following Adrian's pseudocode in DCE video
    for func in prog['functions']:

        used = set()
        dead_idcs = []

        last_length = -1

        def not_dead(inst):
            if 'dest' in inst and inst['dest'] not in used:
                return False
            return True

        while last_length != len(func['instrs']):
            for instr in func['instrs']:
                if 'args' in instr:
                    used |= set(instr['args'])

            last_length = len(func['instrs'])
            func['instrs'] = list(filter(not_dead, func['instrs']))

    json.dump(prog, sys.stdout)


if __name__ == '__main__':
    dce()
