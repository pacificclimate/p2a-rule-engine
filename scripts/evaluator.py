import operator


def get_symbol_value(symbol, rules, variable_getter):
    """Given the name of a terminal symbol in an rule expression, return either
       the parse tree for that symbol if it is a rule either the value of that
       symbol if it is a variable.
    """
    if 'rule_' in symbol:
        return rules[symbol]
    else:
        return variable_getter(symbol)


def cond_operand(cond, t_val, f_val):
    if cond:
        return t_val
    else:
        return f_val


def evaluate_parse_tree(pt, pt_d, variable_getter):
    # base case
    if not isinstance(pt, tuple):
        if isinstance(pt, str):
            # string, needs substitution
            return evaluate_parse_tree(get_symbol_value(pt, pt_d, variable_getter),
                                       pt_d,
                                       variable_getter)
        else:
            # constant
            return pt

    # operator lookup table
    ops = {'+' : operator.add,
           '-' : operator.sub,
           '*' : operator.mul,
           '/' : operator.truediv,
           '>' : operator.gt,
           '>=': operator.ge,
           '<' : operator.lt,
           '<=': operator.le,
           '==': operator.eq
          }

    # check operation
    op = pt[0]

    if op in ops:
        return ops[op](evaluate_parse_tree(pt[1], pt_d, variable_getter),
                       evaluate_parse_tree(pt[2], pt_d, variable_getter))
    elif op == '&&':
        return evaluate_parse_tree(pt[1], pt_d, variable_getter) and \
               evaluate_parse_tree(pt[2], pt_d, variable_getter)
    elif op == '||':
        return evaluate_parse_tree(pt[1], pt_d, variable_getter) or \
               evaluate_parse_tree(pt[2], pt_d, variable_getter)
    elif op == '!':
        return not evaluate_parse_tree(pt[1], pt_d, variable_getter)
    elif op == '?':
        return cond_operand(evaluate_parse_tree(pt[1], pt_d, variable_getter),
                            evaluate_parse_tree(pt[2], pt_d, variable_getter),
                            evaluate_parse_tree(pt[3], pt_d, variable_getter))
