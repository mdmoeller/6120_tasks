#!/usr/bin/python3

# Mark Moeller

import json
import sys


TERM = 'jmp', 'br', 'ret'

COMMUTE = 'add', 'mul', 'eq', 'and', 'or'
ARITH = 'add', 'mul', 'div'


class Value:

    def __init__(self, vals, oper, t,  args):

        # list of all values
        self.values = vals

        # node type of this Value
        self.oper = oper

        # type of this value
        self.t = t

        # list of indeces into vals reperesenting the args to this value
        if oper in COMMUTE:
            self.args = sorted(args)
        else:
            self.args = args

        # this will get set later on, depending on whether this value already
        # exists
        self.canonical = []

    def __eq__(self, other):
        if self.oper != other.oper or self.oper == 'call' or self.t != other.t:
            return False
        
        for i,a in enumerate(self.args):
            if a != other.args[i]:
                return False

        return True


    def __str__(self):
        return '{} {} ({})'.format(self.oper, self.args, self.canonical)

# Return the index of the given val in values (creating one if it doesn't
# exist yet)
def index_of(values, val, name=[]):

    try:
        return values.index(val)  # linear search, eeek
    except ValueError:
        values += [val]
        if name:
            val.canonical = name
        return len(values) - 1
    

# From bril repository
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
            if cur_block:
                yield cur_block

            cur_block = [inst]

    yield cur_block

def lvn():
    prog = json.load(sys.stdin)


    for func in prog['functions']:

        newinstr = []

        print(func['name'], file=sys.stderr)

        # Deal with the weird condition where a variable might be reassigned:
        dests = [instr['dest'] for instr in func['instrs'] if 'dest' in instr]
        all_names = set(dests)
        for args in [instr['args'] for instr in func['instrs'] if 'args' in instr]:
            all_names |= set(args)

        # Return a new name for a given variable needing renaming.
        # After discussion in class, realized this is too conversative (i.e. not
        # necssary).
        def new_name(old_name):
            name = "_" + old_name
            while name in all_names:
                name = "_" + name
            all_names.add(name)
            return name


        for block in form_blocks(func['instrs']):

            # Holds the list of values
            values = []

            # Map variable names to indeces of `values`
            variables = {}

            # Map old names to new names for variables needing renaming
            # renamed = {}
            
            # Mark candidates for renaming
            assigned_later = set()
            for instr in reversed(block):
                if 'dest' in instr:
                    if instr['dest'] in assigned_later:
                        instr['rename'] = True
                    assigned_later.add(instr['dest'])

            for i,instr in enumerate(block):

                if 'op' in instr:

                    # const instruction is special because the args aren't
                    # variable names
                    if instr['op'] == 'const':
                        v = Value(values, 'const', instr['type'], [instr['value']])
                        constval = index_of(values, v, name=instr['dest'])
                        variables[instr['dest']] = constval

                    # id is special in that we can just reuse the value
                    if instr['op'] == 'id' and instr['args'][0] in variables:
                        copyval = variables[instr['args'][0]]
                        variables[instr['dest']] = copyval
                        instr['args'] = [values[copyval].canonical]

                    # The other ops use variable names:
                    elif 'args' in instr:
                        args = []
                        canon_args = []
                        for arg in instr['args']:
                            # if arg in renamed:
                                # arg = renamed[arg]

                            if arg not in variables:
                                v = Value(values, 'nonloc', 'nonloc', [arg])
                                variables[arg] = index_of(values, v, name=arg)
                                
                            idx = variables[arg]
                            args += [idx]
                            canon_args += [values[idx].canonical]

                        # this line is important: update the instruction to
                        # ``canonicalize'' the arguments
                        instr['args'] = canon_args

                    
                        if 'dest' in instr:
                            v = Value(values, instr['op'], instr['type'], args)
                            # if instr['dest'] in renamed:
                                # renamed.pop(instr['dest'])

                            if 'rename' in instr:
                                name = new_name(instr['dest'])
                                # renamed[instr['dest']] = name
                                variables[instr['dest']] = variables[name] = index_of(values, v, name=name)
                                instr['dest'] = name
                                instr.pop('rename')
                            else:
                                variables[instr['dest']] = index_of(values, v, name=instr['dest'])

                newinstr += [instr]
            print('block:', file=sys.stderr)
            for i,v in enumerate(values):
                print('[{}]: {}'.format(i, v), file=sys.stderr)
            print('vars:{}\n'.format(variables), file=sys.stderr)

        func['instrs'] = newinstr

    json.dump(prog, sys.stdout)


if __name__ == '__main__':
    lvn()
