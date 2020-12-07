#!/usr/bin/python3

import sys
import json
from dom import Dominators
from brilpy import *
from functools import reduce

def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:

        # Add dummy id operations for each argument.
        # This is a bit of a hack because of the fact that you can reassign to
        # the args anywhere in the function.
        # We don't want the first block to be a place we can jump to, because
        # we can't have a phi as the first instruction to disambiguate args
        if 'args' in func:
            if func['args']:
                for a in func['args']:
                    func['instrs'] = [{'op':'id', 'args':[a['name']], 'type':a['type'], 'dest':a['name']}] + \
                                     func['instrs']
                func['instrs'] = [{'label':'pre_entry'}] + func['instrs']

        # Next we need to canonicalize labels, in case any labels appear
        # directly in a row, this would break things later
        label_last = False
        last = None
        i = 0
        while i < len(func['instrs']):
            inst = func['instrs'][i]
            if 'label' in inst:
                if label_last:
                    for j in func['instrs']:
                        if 'labels' in j and inst['label'] in j['labels']:
                            labels = []
                            for lbl in j['labels']:
                                if lbl == inst['label']:
                                    labels.append(last['label'])
                                else:
                                    labels.append(lbl)
                            j['labels'] = labels
                    func['instrs'].pop(i)

                else:
                    i += 1
                    last = inst
                    label_last = True
            else:
                i += 1
                label_last = False

        # This last bit is just because even after the above, a valid bril
        # program could end with a label, but we don't want that (i.e., an empty
        # block
        if label_last:
            func['instrs'].append({'op':'nop'});


        g = CFG(func)


        domins = Dominators(func)


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
        for i in range(g.n):
            phis.append({})

        # Following pseudocode from Lesson 5 notes
        # ``Step one''
        for v,vdefs in defs.items():
            for d in vdefs:
                for b in domins.frontier[d]:
                    if v not in phis[b]:
                        phis[b][v] = {'op':'phi', 'args':[], 'labels':[]} # will handle dest/args later

                    if b not in defs[v]:
                        defs[v].append(b)

        # ``Step two''
        stack = {}
        next_name = {}
        for v in defs.keys():
            stack[v] = []
            next_name[v] = 0

        # args' bottom-stack names are their original names
        if 'args' in func:
            for arg in func['args']:
                stack[arg['name']] = [arg['name']]


        def new_name(ogvar):
            n = ogvar + '_' + str(next_name[ogvar])
            next_name[ogvar] += 1
            stack[ogvar].append(n)
            return n

        # b: index of block
        def rename(b):


            # map from vars to count of names pushed (so we can pop them)
            push_count = {}

            for v,p in phis[b].items():
                p['dest'] = new_name(v)

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
                    if instr['dest'] in push_count:
                        push_count[instr['dest']] += 1
                    else:
                        push_count[instr['dest']] = 1

                    instr['dest'] = name

            for s in g.edges[b]:

                for v in set(phis[s].keys()): # (copy keyset so we can remove)

                    # we found a path to this block where it is unassigned: this phi should go away
                    if not stack[v]: 
                        phis[s].pop(v)

                    # otherwise update the var-use to use the current name
                    else:
                        phis[s][v]['args'].append(stack[v][-1])
                        phis[s][v]['labels'].append(g.names[b])

            if b in domins.dom_tree:
                for b_dom in domins.dom_tree[b]:
                    rename(b_dom)

            # pop all the names
            for var,count in push_count.items():
                for j in range(count):
                    stack[var].pop()

        rename(0)

        newinstrs = []

        for i,b in enumerate(g.blocks):
            if 'label' in b[0]:
                newinstrs.append(b[0])
                b.pop(0)
            else:
                newinstrs.append({'label': g.names[i]})

            for v,p in phis[i].items():
                # don't need a phi if only one label or arg
                if len(set(p['labels'])) > 1 and len(set(p['args'])) > 1: 
                    newinstrs.append(p)
                
            newinstrs += b

        func['instrs'] = newinstrs

    json.dump(prog, sys.stdout)



if __name__ == '__main__':
    main()
