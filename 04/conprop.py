#!/usr/bin/python3

# Mark Moeller:
# Computes constant propagation dataflow analysis in bril programs.


import json
import sys


TERM = 'jmp', 'br', 'ret'

# From Lesson 2
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
            if len(cur_block) != 0:
                yield cur_block

            cur_block = [inst]

    if len(cur_block) != 0:
        yield cur_block


# Returns (names, blocks, edges), where:
# names: a list of block names
# blocks: the list of blocks themselves
# edges: idx->idx map of successors
def cfg(func):
    names = []
    blocks = []

    # Map label -> block idx for that label
    labels = {}

    # Edges of the CFG
    edges = {} 

    # When we encounter jumps to labels that haven't appeared yet, add the
    # label here with a list of blocks that need to jump TO that label
    # label -> [list of blocks forward-jumping to it]
    resolve = {} 

    def make_edge(idx, label):
        if label in labels:
            if idx in edges:
                edges[idx].append(labels[label])
            else:
                edges[idx] = [labels[label]]
        else:
            if label in resolve:
                resolve[label].append(idx)
            else:
                resolve[label] = [idx]

    for i,block in enumerate(form_blocks(func['instrs'])):

        blocks.append(block)

        name = "b" + str(i)

        if 'label' in block[0]:
            name = block[0]['label']
            labels[name] = i

        names.append(name)

        if block[-1]['op'] == 'br' or block[-1]['op'] == 'jmp':
            for label in block[-1]['labels']:
                make_edge(i, label)

        elif block[-1]['op'] != 'ret':
            edges[i] = [i+1]


    for lab,idcs in resolve.items():
        for idx in idcs:
            if idx in edges:
                edges[idx].append(labels[lab])
            else:
                edges[idx] = [labels[lab]]

    # If we added i+1 for the last block, remove it (there is no successor)
    if (len(names)-1) in edges and len(names) in edges[len(names)-1]:
        edges.pop(len(names)-1)

    return (names, blocks, edges)

# ------------------------------------------------------------------------------
# Worklist functions for computing `defined variables'
# ------------------------------------------------------------------------------

def defvars_init(func, graph):
    in_b = [set([a['name'] for a in func['args']])]
    out_b = [set()]
    for i in range(len(graph[0])-1):
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

    for i in range(len(graph[0])-1):
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
# Worklist function
# func: the function object (as loaded from json)
# init: (func, graph) -> (in_b, out_b): Computes initial datastructures. in_b
#                                       and out_b are each arrays of size
#                                       len(blocks).
# xfer: (in_b, block) -> out_b:         Compute transfer for a single block.
# merge: List of out_b -> in_b:         Given a list of predecessors' out_b's,
#                                       compute a single in_b.
# ------------------------------------------------------------------------------

def run_worklist(func, init, xfer, merge):
    graph = (names, blocks, edges) = cfg(func)

    # compute edges_r to get predecessors
    preds = {}
    for k,v in edges.items():
        for d in v:
            if d in preds:
                preds[d] += [k]
            else:
                preds[d] = [k]

    (in_b, out_b) = init(func, graph)

    worklist = list(range(len(names)))

    while worklist:
        b = worklist[0]
        worklist = worklist[1:]

        in_b[b] = merge([out_b[x] for x in preds[b]]) if b in preds else {}

        out_b_copy = out_b[b].copy()

        out_b[b] = xfer(in_b[b], blocks[b])

        if out_b[b] != out_b_copy and b in edges:
            worklist += edges[b]

    return (in_b, out_b)
        


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
        g = cfg(func)
        
        (in_b, out_b) = run_worklist(func, cp_init, cp_xfer, cp_merge)

        for i,name in enumerate(g[0]):
            print("  {}:\n    consts in: {}\n    consts out:{}\n\n".format(name,
                pretty_dict(in_b[i]), pretty_dict(out_b[i])))



if __name__ == '__main__':
    main()
