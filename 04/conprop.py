#!/usr/bin/python3

# Mark Moeller:
# Computes constant propagation dataflow analysis in bril programs.


import json
import sys
from brilpy import *

# ------------------------------------------------------------------------------
# Worklist functions for computing `defined variables'
# ------------------------------------------------------------------------------

def defvars_init(func, graph):
    in_b = [set([a['name'] for a in func['args']])]
    out_b = [set()]
    for i in range(graph.n-1):
        in_b.append(set())
        out_b.append(set())
    return (in_b, out_b)

# Transfer function for defined variables
def defvars_xfer(in_b, block):
    out_b = set(in_b)
    for inst in block:
        if 'dest' in inst:
            out_b.add(inst['dest'])
    return out_b

def defvars_merge(pred_list):
    result = set()
    for p in pred_list:
        result |= p
    return result

# ------------------------------------------------------------------------------
# Worklist functions for computing `constant propagation'
#
# For constant propagation, we'll use a map from variable names to constant
# values, with a name holding 'None' in the map if we know it is NOT constant.
# ------------------------------------------------------------------------------

def cp_init(func, graph):
    in_b = []
    out_b = []

    in_b.append({})
    out_b.append({})

    if 'args' in func:
        for arg in func['args']:
            in_b[0][arg['name']] = None # Args are NOT constant

    for i in range(graph.n - 1):
        in_b.append({})
        out_b.append({})
    return (in_b, out_b)

def cp_xfer(in_b, block):

    out_b = {}
    for k,v in in_b.items():
        out_b[k] = v

    for inst in block:
        if 'op' in inst and 'dest' in inst and inst['type'] == 'int':
            if inst['op'] == 'const':
                out_b[inst['dest']] = inst['value']

            elif inst['op'] == 'call':
                out_b[inst['dest']] = None # This analysis is intra-procedural only

            else:
                if len(inst['args']) == 1:
                    # If the one arg is already guaranteed constant, then propagate
                    if inst['args'][0] in out_b and inst['args'][0] != None:
                        out_b[inst['dest']] = out_b[inst['args'][0]]
                    # Otherwise, mark this var. non-constant
                    else:
                        out_b[inst['dest']] = None

                else:
                    # For two args: if both constant, we can fold and propagate
                    if inst['args'][0] in out_b and out_b[inst['args'][0]] != None and \
                       inst['args'][1] in out_b and out_b[inst['args'][1]] != None:
                        
                        op = { 'add' : (lambda x, y: x + y),
                               'mul' : (lambda x, y: x * y),
                               'sub' : (lambda x, y: x - y),
                               'div' : (lambda x, y: int(x / y)) }

                        out_b[inst['dest']] = op[inst['op']](out_b[inst['args'][0]], 
                                                             out_b[inst['args'][1]])

                    # Similar to above, in any other case, mark non-constant
                    else:
                        out_b[inst['dest']] = None

    return out_b

# pred_list: list of maps(var -> value)
def cp_merge(pred_list):

    result = {}

    all_defined_vars = set()

    for p in pred_list:
        all_defined_vars |= p.keys()

    for var in all_defined_vars:

        # Check that the values assigned to this variable *in the predecessors
        # in which it is assigned* are all the same, and not None. If so, it is
        # guaranteed to be a constant.
        vals = [p[var] for p in pred_list if var in p]

        if vals.count(vals[0]) == len(vals) and None not in vals:
            result[var] = vals[0]
        else:
            result[var] = None

    return result
    

        

# ------------------------------------------------------------------------------

def pretty_dict(d):
    s = ""
    for k in d.keys():
        s += "{}: {}  ".format(k, d[k] if d[k] != None else '?')
    return s

def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:

        print("func: {}".format(func['name']))
        g = CFG(func)
        
        # (in_b, out_b) = run_worklist(func, cp_init, cp_xfer, cp_merge)
        (in_b, out_b) = run_worklist(func, rd_init, rd_xfer, rd_merge)

        for i,name in enumerate(g.names):
            print("  {}:\n    consts in: {}\n    consts out:{}\n\n".format(name,
                pretty_dict(in_b[i]), pretty_dict(out_b[i])))



if __name__ == '__main__':
    main()
