import operator
from decimal import Decimal
import logging


logger = logging.getLogger('scripts')
operands = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq
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


def cond_operator(cond, t_val, f_val):
    """Mimic the functionality of the conditional operator
       'cond ? t_val : f_val'
    """
    if cond:
        return t_val
    else:
        return f_val


def evaluate_rule(rule, rules, variable_getter):
    """This method uses a helper method to recursively compute the value of the
       rule expression.
    """

    def evaluate_expression(expression):
        """Evaluate the given expression."""
        # base case
        if isinstance(expression, float) or isinstance(expression, int):
            return Decimal(expression)
        elif isinstance(expression, Decimal):
            return expression

        # check operation
        operand = expression[0]

        if operand in operands:
            return operands[operand](evaluate_expression(expression[1]),
                                     evaluate_expression(expression[2]))
        elif operand == '&&':
            return evaluate_expression(expression[1]) and \
                   evaluate_expression(expression[2])
        elif operand == '||':
            return evaluate_expression(expression[1]) or \
                   evaluate_expression(expression[2])
        elif operand == '!':
            return not evaluate_expression(expression[1])
        elif operand == '?':
            return cond_operator(evaluate_expression(expression[1]),
                                 evaluate_expression(expression[2]),
                                 evaluate_expression(expression[3]))
        elif isinstance(expression, str):
            return evaluate_expression(get_symbol_value(expression,
                                                        rules,
                                                        variable_getter))
        else:
            logger.warning('Unable to process expression')
            return None

    return evaluate_expression(rule)
