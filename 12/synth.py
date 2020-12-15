import z3
import lark
import sys
from functools import reduce

GRM = """
?start: sum
  | sum "?" sum ":" sum -> if

?sum: term
  | sum "+" term        -> add
  | sum "-" term        -> sub

?term: item
  | term "*" item       -> mul
  | term "/" item       -> div
  | term ">>" item      -> shr
  | term "<<" item      -> shl

?item: NUMBER           -> num
  | "-" item            -> neg
  | CNAME               -> var
  | "(" start ")"

%import common.NUMBER
%import common.WS
%import common.CNAME
%ignore WS
""".strip()

def tern(cond, first, second):
    # print('cond {} {}'.format(cond, type(cond)))
    # print('first {} {}'.format(first, type(first)))
    # print('second {} {}'.format(second, type(second)))
    return (cond != 0) * first + (cond == 0) * second

def solve(phi):
    """ Modified from Adrian's examples
    phi: list of clauses to solve
    """
    s = z3.Solver()
    for p in phi:
        s.add(p)
    r = s.check()
    if r == z3.sat:
        return s.model()
    else:
        return r

def pretty(tree, subst={}, paren=False):
    """From Adrian's examples

    If `paren` is true, then loose-binding expressions are
    parenthesized. We simplify boolean expressions "on the fly."
    """

    # Add parentheses?
    if paren:
        def par(s):
            return '({})'.format(s)
    else:
        def par(s):
            return s

    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr'):
        lhs = pretty(tree.children[0], subst, True)
        rhs = pretty(tree.children[1], subst, True)
        c = {
            'add': '+',
            'sub': '-',
            'mul': '*',
            'div': '/',
            'shl': '<<',
            'shr': '>>',
        }[op]
        return par('{} {} {}'.format(lhs, c, rhs))
    elif op == 'neg':
        sub = pretty(tree.children[0], subst)
        return '-{}'.format(sub, True)
    elif op == 'num':
        return tree.children[0]
    elif op == 'var':
        name = tree.children[0]
        return str(subst.get(name, name))
    elif op == 'if':
        cond = pretty(tree.children[0], subst)
        true = pretty(tree.children[1], subst)
        false = pretty(tree.children[2], subst)
        return par('{} ? {} : {}'.format(cond, true, false))

def model_values(model):
    """Get the values out of a Z3 model.
    """
    return {
        d.name(): model[d]
        for d in model.decls()
    }

def interp(tree, lookup):
    """from Adrian's examples:
    Interprets a parse tree from our toy language using lookup for variables
    """
    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr'):
        lhs = interp(tree.children[0], lookup)
        rhs = interp(tree.children[1], lookup)
        if op == 'add':
            return lhs + rhs
        elif op == 'sub':
            return lhs - rhs
        elif op == 'mul':
            return lhs * rhs
        elif op == 'div':
            return lhs / rhs
        elif op == 'shl':
            return lhs << rhs
        elif op == 'shr':
            return lhs >> rhs
    elif op == 'neg':
        sub = interp(tree.children[0], lookup)
        return -sub
    elif op == 'num':
        return int(tree.children[0])
    elif op == 'var':
        return lookup(tree.children[0])
    elif op == 'if':
        cond = interp(tree.children[0], lookup)
        true = interp(tree.children[1], lookup)
        false = interp(tree.children[2], lookup)
        return tern(cond, true, false)


def z3expr(tree, variables = None):
    """z3expr from Adrian's examples:
    Returns a z3 expression along with map from varnames to free vars in expr
    """

    variables = dict(variables) if variables else {}

    def get_var(name):
        if name in variables:
            return variables[name]
        else:
            v = z3.BitVec(name, 8)
            variables[name] = v
            return v

    return interp(tree, get_var), variables

def main():
    parser = lark.Lark(GRM)

    tree_spec = parser.parse(sys.stdin.readline())
    spec, vars1 = z3expr(tree_spec)

    tree_sketch = parser.parse(sys.stdin.readline())
    sketch, vars2 = z3expr(tree_sketch, vars1)

    specvars =  {k: v for k, v in vars1.items() if not k.startswith('h')}
    sketchvars =  {k: v for k, v in vars2.items() if not k.startswith('h')}

    next_const = 0

    def varswitch(orig_vars):
        """ Return both a string and z3 representation of the `variable switch'
        constructed for the list of variable options"""
        if not orig_vars:
            print("synth.py: cannot have variable type with no variables", file=sys.stderr)
            sys.exit(1)
        if len(orig_vars) == 1:
            return orig_vars.popitem()
        else:
            nonlocal next_const 
            cstr = 'c' + str(next_const)
            c = z3.BitVec(cstr, 8)
            next_const += 1

            (k, v) = orig_vars.popitem()
            (rk, rv) = varswitch(orig_vars)
            return ('(' + cstr + '? ' + k + ' : ' + rk + ')', tern(c, v, rv))

    goal = (spec == sketch)

    clauses = []
    for k, v in vars2.items():
        if k.startswith('v'): # Needs a variable switch
            kvar = z3.BitVec(k, 8)

            # Note first `==` here is boolean equivalence, second is domain equality
            (s, z) = varswitch(specvars.copy())
            print(k + ' == ' + s)
            clauses.append(kvar == z)

    # All the variable 'assignments' satisfy the equality
    goal = z3.Implies(reduce(z3.And, clauses), goal)

    # The implication works for any valuation of the original variables and v's
    goal = z3.ForAll(list(sketchvars.values()), goal)

    model = solve([goal])
    if isinstance(model, z3.z3.ModelRef):
        print('Success! {}'.format(model))
        print(pretty(tree_spec))
        print(pretty(tree_sketch, model_values(model)))
    else:
        print(model)


if __name__ == '__main__':
    main()
