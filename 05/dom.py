#!/usr/bin/python3

import sys
import json
from brilpy import *
from functools import reduce

def dom(func):
    g = CFG(func)

    # First compute dominators
    # IMPORTANT: This computes, for each block, the set of blocks that dominate
    # it, not the other way around
    doms = []
    doms.append(set([0])) # Entry block is special, it's its own dominator
    for i in range(1,g.n):
        doms.append(set(range(g.n)))

    order = g.rpo()

    # for i in order:
        # print(g.names[i])

    # print("doms: {}".format(doms))

    changed = True
    while changed:
        changed = False
        for i in order:
            d = {i}
            if g.preds[i]:
                d |= reduce(set.intersection, [doms[p] for p in g.preds[i]], set(range(g.n)))

            if d != doms[i]:
                changed = True
                doms[i] = d

        # print("doms: {}".format(doms))

    # Compute the "other way around" (from above), that is, for each block, the
    # set of blocks this block dominates
    dom_by = []
    for i in range(g.n):
        dom_by.append(set())
    
    for i,d in enumerate(doms):
        for mbr in d:
            dom_by[mbr].add(i)



    # Compute the dominance tree (slowly?)
    dt_parent = {0: 0}
    rank = {0: 0}
    while len(dt_parent.keys()) < g.n:
        # print(dt_parent)
        for i in range(g.n):
            if i not in dt_parent and len(doms[i].difference(set(dt_parent.keys()))) == 1:
                dt_parent[i] = max(doms[i] & dt_parent.keys(), key=(lambda x: rank[x]))
                rank[i] = rank[dt_parent[i]] + 1

    dt_parent.pop(0)

    dom_tree = {}
    for i,p in dt_parent.items():
        if p in dom_tree:
            dom_tree[p].append(i)
        else:
            dom_tree[p] = [i]


    # Compute dominance frontier
    frontier = []
    for i in range(g.n):
        frontier.append(set())

    for i,d in enumerate(doms):
        # Union of dominators for this node's preds
        pre_doms = reduce(set.union, [doms[p] for p in g.preds[i]], set())
        # Subtract out dominators for this node
        pre_doms = pre_doms.difference(doms[i])

        # This node is in the frontier for the remaining nodes:
        for p in pre_doms:
            frontier[p].add(i)

    return (doms, dom_by, dom_tree, frontier)




def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:

        print("**Function: {}".format(func['name']))

        g = CFG(func)

        f = open("graphs/" + func['name'] + "-cfg.dot", 'w')
        f.write(g.to_dot())
        f.close()
        print(g.to_dot())

        g.print_names()
        print("  edges: {}".format(g.edges))
        print("  preds: {}".format(g.preds))

        (doms, dom_by, dom_tree, frontier) = dom(func)

        print("\n\n  doms:\n{}\n".format(doms))
        for k,v in enumerate(doms):
            print("    {}: ".format(g.names[k]), end="")
            for mbr in v:
                print("{} ".format(g.names[mbr]), end="")
            print("")

        # print("dom tree:\ndigraph g {")

        print("  domtree:")
        f = open("graphs/" + func['name'] + "-dt.dot", 'w')
        print("digraph g {")
        f.write("digraph g {\n")
        for k,v in dom_tree.items():
            for mbr in v:
                print("{} -> {};".format(g.names[k], g.names[mbr]))
                f.write("{} -> {};\n".format(g.names[k], g.names[mbr]))
        print("}")
        f.write("}\n")
        f.close()

        print("\n\n  dominance frontier:")
        for k,v in enumerate(frontier):
            print("    {}: ".format(g.names[k]), end="")
            for mbr in v:
                print("{} ".format(g.names[mbr]), end="")
            print("")

if __name__ == '__main__':
    main()
