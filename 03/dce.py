#!/usr/bin/python3

# Mark Moeller
# Approach following Adrian Sampson DCE lesson videos; implementation mine.

import json
import sys


TERM = 'jmp', 'br', 'ret'

# From bril repository
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



    for func in prog['functions']:

        newinstr = []

        # Local DCE in each block first (second part of Adrian DCE video):
        for block in form_blocks(func['instrs']):
            dead_idcs = True

            while dead_idcs:
                dead_idcs = []
                unused = {}

                for i,inst in enumerate(block):

                    if 'args' in inst:
                        for arg in inst['args']:
                            if arg in unused:
                                unused.pop(arg)

                    if 'dest' in inst:
                        if inst['dest'] in unused:
                            dead_idcs.append(unused[inst['dest']])
                        unused[inst['dest']] = i

                for i in reversed(dead_idcs):
                    block.pop(i)

            newinstr += block

        func['instrs'] = newinstr

        # Global DCE (first part of Adrian DCE video):
        used = set()
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

            used = set()

    json.dump(prog, sys.stdout)


if __name__ == '__main__':
    dce()
