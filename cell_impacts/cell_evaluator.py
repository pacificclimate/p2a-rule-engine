import numpy as np
import operator
import logging

logger = logging.getLogger("scripts")

# Operator mappings
operands = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}

def cond_operator(cond, t_val, f_val):
  return np.where(cond, t_val, f_val)


def evaluate_rule(rule, rule_getter, variable_getter):
    # Evaluate a rule for each cell in the grid.
    def evaluate_expression(expression):
        """Recursively evaluate an expression."""
        logger.debug(f"Evaluating expression: {expression}")

        # Base case: scalar or NumPy array
        if isinstance(expression, (float, int, np.ndarray)):
            logger.debug(f"Expression is scalar or array. Type: {type(expression)}")
            return np.array(expression)

        # Check operation
        operand = expression[0]

        if operand in operands:
            # Arithmetic or comparison
            logger.debug(f"Operand: {operand}")
            return operands[operand](
                evaluate_expression(expression[1]), evaluate_expression(expression[2])
            )
        elif operand == "&&":
            # Logical AND
            return np.logical_and(
                evaluate_expression(expression[1]), evaluate_expression(expression[2])
            )
        elif operand == "||":
            # Logical OR
            return np.logical_or(
                evaluate_expression(expression[1]), evaluate_expression(expression[2])
            )
        elif operand == "!":
            # Logical NOT
            return np.logical_not(evaluate_expression(expression[1]))
        elif operand == "?":
            # Conditional operator
            return cond_operator(
                evaluate_expression(expression[1]),
                evaluate_expression(expression[2]),
                evaluate_expression(expression[3]),
            )
        elif isinstance(expression, str):
            # Variable or nested rule
            logger.debug(f"Evaluating symbol: {expression}")
            resolved_value = get_symbol_value(expression, rule_getter, variable_getter)
            logger.debug(f"Resolved symbol '{expression}' to: {resolved_value}")
            return evaluate_expression(resolved_value)
        else:
            logger.error(f"Unable to process expression: {expression}")
            raise NotImplementedError(f"Unknown operation: {operand}")

    return evaluate_expression(rule)


def get_symbol_value(symbol, rule_getter, variable_getter):
    # Resolve variable or nested rule.
    logger.debug(f"Resolving symbol: {symbol}")

    if "rule_" in symbol:
        # Fetch the nested rule using rule_getter
        value = rule_getter(symbol)
        logger.debug(f"Resolved nested rule '{symbol}' to: {value} (Type: {type(value)})")
        
        # If the resolved value is a tuple, evaluate it as a rule
        if isinstance(value, tuple):
            logger.debug(f"Evaluating nested rule '{symbol}' because it is a tuple.")
            value = evaluate_rule(value, rule_getter, variable_getter)
        
        # If the resolved value is a string, it represents another rule
        elif isinstance(value, str) and "rule_" in value:
            logger.debug(f"Resolved '{symbol}' to another rule '{value}'. Recursively evaluating.")
            value = get_symbol_value(value, rule_getter, variable_getter)
    
    else:
        # Resolve variable directly
        value = variable_getter(symbol)
        logger.debug(f"Resolved variable '{symbol}' to: {value} (Type: {type(value)})")

    # Validate the type of the resolved value
    if not isinstance(value, (np.ndarray, int, float)):
        logger.error(f"Invalid type for symbol '{symbol}': {type(value)}. Expected NumPy array or scalar.")
        raise ValueError(f"Invalid type for symbol '{symbol}': {type(value)}. Expected NumPy array or scalar.")

    return value
