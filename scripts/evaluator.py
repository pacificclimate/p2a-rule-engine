import operator


operands = {
    '+' : operator.add,
    '-' : operator.sub,
    '*' : operator.mul,
    '/' : operator.truediv,
    '>' : operator.gt,
    '>=': operator.ge,
    '<' : operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '&&': operator.and_,
    '||': operator.or_
}


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


def evaluate_rule(rule, rules, variable_getter):
    def evaluate_symbol(symbol):
        """Given a variable return the value

           This method recursively navigates a parse tree and once it reaches the
           leaves it evaluates the expression.
        """
        # base case
        if not isinstance(symbol, tuple):
            if isinstance(symbol, str):
                return evaluate_symbol(get_symbol_value(symbol, rules, variable_getter))
            else:
                return symbol

        # check operation
        operand = symbol[0]

        if operand in operands:
            return operands[operand](evaluate_symbol(symbol[1]), evaluate_symbol(symbol[2]))
        elif operand == '!':
            return not evaluate_symbol(symbol[1])
        elif operand == '?':
            return cond_operand(evaluate_symbol(symbol[1]),
                                evaluate_symbol(symbol[2]),
                                evaluate_symbol(symbol[3]))
    return evaluate_symbol(rule)
