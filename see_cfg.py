#!/usr/bin/python3

from brilpy import *
import os
import json
import sys

def main():

    prog = json.load(sys.stdin)

    for func in prog['functions']:

        g = CFG(func)

        print('function: {}'.format(func['name']))
        
        f = open(".tmp.dot", 'w')
        print(g.to_dot(), file=f)
        f.close()

        os.system("dot -Tpdf < .tmp.dot > .tmp.pdf")
        os.system("evince .tmp.pdf")

    os.system("rm .tmp.dot .tmp.pdf")

if __name__ == '__main__':
    main()
