#!/usr/bin/python3

# Mark Moeller:

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

class CFG:
    # Constructs a new cfg (names, blocks, edges), where:
# names: a list of block names
# blocks: the list of blocks themselves
# edges: idx->idx map of successors
    def __init__(self, func):
        self.names = []
        self.blocks = []

        # Map label -> block idx for that label
        labels = {}

        # Edges of the CFG
        self.edges = []

        # When we encounter jumps to labels that haven't appeared yet, add the
        # label here with a list of blocks that need to jump TO that label
        # label -> [list of blocks forward-jumping to it]
        resolve = {} 

        def make_edge(idx, label):
            if label in labels:
                self.edges[idx].append(labels[label])
            else:
                if label in resolve:
                    resolve[label].append(idx)
                else:
                    resolve[label] = [idx]

        for i,block in enumerate(form_blocks(func['instrs'])):

            self.blocks.append(block)
            self.edges.append([])

            name = "b" + str(i)

            if 'label' in block[0]:
                name = block[0]['label']
                labels[name] = i

            self.names.append(name)

            if 'op' in block[-1] and (block[-1]['op'] == 'br' or block[-1]['op'] == 'jmp'):
                for label in block[-1]['labels']:
                    make_edge(i, label)

            elif 'op' in block[-1] and block[-1]['op'] != 'ret':
                self.edges[i] = [i+1]

        self.n = len(self.names)

        for lab,idcs in resolve.items():
            for idx in idcs:
                self.edges[idx].append(labels[lab])

        # If we added i+1 for the last block, remove it (there is no successor)
        if self.n in self.edges[-1]:
            self.edges[-1] = []

        # compute edges_r to get predecessors
        self.preds = []
        for i in range(self.n):
            self.preds.append([])

        for k,v in enumerate(self.edges):
            for d in v:
                self.preds[d].append(k)

    # Return the indeces in reverse-post-order 
    def rpo(self):
        WHITE = 0
        GRAY = 1
        BLACK = 2

        visited = []
        colors = [WHITE] * self.n

        def dfs_visit(node):
            if colors[node] == WHITE:
                colors[node] = GRAY
                if node in self.edges:
                    for v in self.edges[node]:
                        dfs_visit(v)
                colors[node] = BLACK
                visited.append(node)

        for i in range(self.n):
            dfs_visit(i)

        return visited

    def to_dot(self):
        s = "digraph g {\n"

        for u,nbrs in enumerate(self.edges):
            for v in nbrs:
                s += self.names[u] + " -> " + self.names[v] + ";\n"

        s += "}\n"
        return s

    def print_names(self):
        for i,n in enumerate(self.names):
            print("{} {}".format(i, n))
