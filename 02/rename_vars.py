#!/usr/bin/python3

# This program takes a bril program in json, looks at each function and renames
# all the labels to label0, label1, etc., and renames each variable to v0, v1,
# etc. The names restart at each new function. This change should not change the
# behavior of the program at all.

import json
import sys

def rename_vars():
    prog = json.load(sys.stdin)

    for func in prog['functions']:

        # Map from old variable names to new ones
        variables = {}

        # Map from old label names to new ones
        labels = {}


        if 'args' in func:
            for arg in func['args']:
                variables[arg['name']] = "v{}".format(len(variables))
                arg['name'] = variables[arg['name']]


        for inst in func['instrs']:
            
            if 'op' in inst:
                if 'dest' in inst:
                    if inst['dest'] not in variables:
                        variables[inst['dest']] = "v{}".format(len(variables))
                    inst['dest'] = variables[inst['dest']]

                if 'args' in inst:
                    newargs = []
                    for arg in inst['args']:
                        if arg not in inst['args']:
                            print("what is: {}", arg)
                            sys.exit(1)
                        newargs.append(variables[arg])
                    inst['args'] = newargs

                if 'labels' in inst:
                    newlabels = []
                    for label in inst['labels']:
                        if label not in labels:
                            labels[label] = "label{}".format(len(labels))
                        newlabels.append(labels[label])
                    inst['labels'] = newlabels


            else: # label
                if inst['label'] not in labels:
                    labels[inst['label']] = "label{}".format(len(labels))
                inst['label'] = labels[inst['label']]
            

    json.dump(prog, sys.stdout, indent=2, sort_keys=True)



if __name__ == '__main__':
    rename_vars()
