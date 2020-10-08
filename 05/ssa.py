#!/usr/bin/python3

import sys
import json
import dom
from brilpy import *
from functools import reduce




def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:

        g = CFG(func)

        # Get all the dominance information
        (doms, dom_by, domtree, frontier) = dom.dom(func)

        defs = {}
        for i,b in enumerate(g.blocks):
            if i == 0 and 'args' in func:
                for arg in func['args']:
                    defs[arg['name']] = [i]

            for instr in b:
                if 'dest' in instr:
                    if instr['dest'] in defs:
                        defs[instr['dest']].append(i)
                    else:
                        defs[instr['dest']] = [i]

        # for each block, these are the phis we'll add at the end. Each has a
        # map from orig.var -> to a map that will become the instruction itself,
        phis = []
        # for each block, a map from var -> set of blocks that have defns
        phis_added = []
        for i in range(g.n):
            phis.append({})
            phis_added.append({})

        # Following pseudocode from Lesson 5 notes
        # ``Step one''
        for v,vdefs in defs.items():
            for d in vdefs:
                for b in frontier[d]:
                    if v in phis_added[b]:
                        phis_added[b][v].add(d)
                    else:
                        phis_added[b][v] = set([d])

                    defs[v].append(b)

        # ``Step two''
        stack = {}
        next_name = {}
        for v in defs.keys():
            stack[v] = [v]  # everything starts with original name
            next_name[v] = 0


        def new_name(ogvar):
            n = ogvar + '_' + str(next_name[ogvar])
            next_name[ogvar] += 1
            return n

        # for i,p in enumerate(phis_added):
            # print("{} {}".format(i, p))

        # b: index of block
        def rename(b):

            # map from vars to count of names pushed (so we can pop them)
            push_count = {}

            for p in phis[b]
            for instr in g.blocks[b]:

                # replace old names with stack names
                if 'args' in instr:
                    newargs = []
                    for arg in instr['args']:
                        newargs.append(stack[arg][-1])
                    instr['args'] = newargs

                # replace destination with new name (and push onto stack)
                if 'dest' in instr:
                    name = new_name(instr['dest'])
                    stack[instr['dest']].append(name)
                    if instr['dest'] in push_count:
                        push_count[instr['dest']] += 1
                    else:
                        push_count[instr['dest']] = 1

                    instr['dest'] = name

            for s in g.edges[b]:
                for v in phis_added[s].keys():
                    if v in phis[s]:
                        phis[s][v].append((stack[v][-1], g.names[b]))
                    else:
                        phis[s][v] = [(stack[v][-1], g.names[b])]

            if b in domtree:
                for b_dom in domtree[b]:
                    rename(b_dom)

            # pop all the names
            for var,count in push_count.items():
                for j in range(count):
                    stack[var].pop()

        rename(0)

        newinstrs = []

        for i,b in enumerate(g.blocks):
            if 'label' in b[0]:
                # print("label={} instr={}".format(b[0]['label'], b[0]))
                newinstrs.append(b[0])
                b.pop(0)
            else:
                newinstrs.append({'label': g.names[i]})

            for v,args in phis[i].items():
                if len(phis_added[i][v]) > 1: # don't need a phi if only one label
                    inst = {'op': 'phi', 'dest': v, 'labels':[], 'args':[]}
                    for arg in args:
                        inst['args'].append(arg[0])
                        inst['labels'].append(arg[1])
                    newinstrs.append(inst)
                
            newinstrs += b

        func['instrs'] = newinstrs

    json.dump(prog, sys.stdout)



if __name__ == '__main__':
    main()
