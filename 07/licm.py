#!/usr/bin/python3
from brilpy import *
from dom import Dominators
from functools import reduce


def main():

    prog = json.load(sys.stdin)

    for func in prog['functions']:

        g = CFG(func)
        doms = Dominators(func)

        natloops = []

        for u,nbrs in enumerate(g.edges):
            for v in nbrs:
                if v in doms.doms[u]:
                    # v dominates u
                    # u -> v is the backedge
                    natloop = list(doms.doms[u].intersection(doms.dom_by[v]))
                    natloop.remove(v)
                    natloop = [v] + natloop
                    natloops.append(natloop)

        # Combine loops that have the same header:
        natloops.sort(key=(lambda x: x[0]))
        i = 0
        while i < len(natloops):
            head = natloops[i][0]
            j = i+1
            while j < len(natloops) and head == natloops[j][0]:
                for k in natloops[j]:
                    if k not in natloops[i]:
                        natloops[i].append(k)
                natloops.pop(j)
            i = j

        (in_b, out_b) = run_worklist(func, rd_init, rd_xfer, rd_merge)

        for loop in natloops:

            exits = []
            for i in loop:
                if set(g.edges[i]).difference(loop):
                    exits.append(i)

            dom_all_exits = reduce(set.intersection, [doms.doms[x] for x in exits], set(range(g.n)))
            eligible_for_motion = dom_all_exits.intersection(loop)

            header = loop[0] # block idx of the header
            preheader = [] # list of instructions that will go in the preheader

            loopinvariant = set() # set of vars to check against
            move_list = [] # list of tuples: (block_idx, instr_idx, instr)

            # Iterate to convergeance:
            changed = True
            while changed:
                changed = False

                # Go through all the instructions in the loop looking for loop
                # invariant ones
                for idx in loop:
                    for i,inst in enumerate(g.blocks[idx]):
                        if 'dest' in inst and 'args' in inst and inst['op'] != 'phi'  \
                        and inst['op'] != 'div' and (idx, i, inst) not in move_list:
                            args_invar = True

                            for x in inst['args']:
                                args_invar = args_invar and (x in loopinvariant
                                        or out_b[idx][x] not in loop)
                            if args_invar:
                                loopinvariant.add(inst['dest'])
                                if idx in eligible_for_motion:
                                    changed = True
                                    move_list.append((idx, i, inst))


            # Form/insert preheader
            if move_list:
                # Sort back to front by inst index, so we can delete easily
                move_list.sort(key=(lambda x: x[1]), reverse=True)
                hdr_label = g.blocks[header][0]['label']
                prehdr_label = '_pre_' + hdr_label
                preheader = [{'label':prehdr_label}]
                for tup in move_list:
                    (idx, i, inst) = tup
                    preheader.append(inst)
                    g.blocks[idx].pop(i)

                # Update the labels of the non-loop predecessors of header to
                # goto preheader
                for p in g.preds[header]:
                    if p not in loop and 'labels' in g.blocks[p][-1]:
                        new_labels = []
                        for lbl in g.blocks[p][-1]['labels']:
                            if lbl == g.blocks[header][0]['label']:
                                new_labels.append(prehdr_label)
                            else:
                                new_labels.append(lbl)
                        g.blocks[p][-1]['labels'] = new_labels

                loop_labels = set([g.blocks[i][0]['label'] for i in loop])

                # Also need to update phis (if any) in header to come from
                # preheader instead of anywhere outside the loop
                i = 0
                while 'label' in g.blocks[header][i]:
                    i += 1

                while i < len(g.blocks[header]) and 'op' in g.blocks[header][i] and \
                      g.blocks[header][i]['op'] == 'phi':

                    new_labels = []
                    for lbl in g.blocks[header][i]['labels']:
                        if lbl in loop_labels:
                            new_labels.append(lbl)
                        else:
                            new_labels.append(prehdr_label)
                    g.blocks[header][i]['labels'] = new_labels
                    i += 1

                # Prepend the header to the old block
                g.blocks[header] = preheader + g.blocks[header]


            func['instrs'] = reduce(lambda x,y: x+y, [g.blocks[i] for i in range(g.n)], [])

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
