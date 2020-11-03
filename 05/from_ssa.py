#!/usr/bin/python3

import sys
import json
from brilpy import *
from functools import reduce

TERM = 'jmp', 'br', 'ret'

def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:

        g = CFG(func)

        # First compute a map from label -> block idx
        # Note: we assume every block in SSA form has a label (is this true?)
        block_by_label = {}
        term = []
        for i,b in enumerate(g.blocks):
            block_by_label[b[0]['label']] = i

            # also temporarily save the TERM instruction (so when we add id's we
            # can just tack them on the end)... this is a bit awkward
            if 'op' in b[-1] and b[-1]['op'] in TERM:
                term.append(b.pop())
            else:
                term.append(None)
        
        # print(term)

        for i,b in enumerate(g.blocks):
            if len(b) == 1:
                continue

            j = 1
            while j < len(b) and 'op' in b[j] and b[j]['op'] == 'phi':
                for k in range(len(b[j]['args'])):
                    inst = {'op': 'id', 'dest': b[j]['dest'],
                            'args':[b[j]['args'][k]]}
                    g.blocks[block_by_label[b[j]['labels'][k]]].append(inst)

                j += 1
        
        # write changes, omitting phis
        newinstr = []
        for i,b in enumerate(g.blocks):
            for inst in b:
                if not ('op' in inst and inst['op'] == 'phi'):
                    newinstr.append(inst)
            if term[i]:
                newinstr.append(term[i])

        func['instrs'] = newinstr

    json.dump(prog, sys.stdout)



if __name__ == '__main__':
    main()
