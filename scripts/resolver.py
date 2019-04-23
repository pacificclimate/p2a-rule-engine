from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from parser import build_parse_tree
from evaluator import evaluate_rule
from fetch_data import get_dict_val, read_csv, get_variables


def setup_logging(log_level):
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',
                                  "%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger('scripts')
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level))
    return logger


def resolve_rules(csv, date_range, region, ensemble, connection_string, log_level='INFO'):
    logger = setup_logging(log_level)

    # read csv
    logger.info('Reading {}'.format(csv))
    rules = read_csv(csv)

    # create parse tree dictionary and gather unique variables
    logger.info('Building parse tree')
    parse_trees = {}
    variables = set()
    for rule, condition in rules.items():
        try:
            parse_trees[rule], vars = build_parse_tree(condition)
        except SyntaxError as e:
            logger.warning('{}, rule will be excluded'.format(e))
            continue

        # add unique variables to set
        for var in vars:
            variables.add(var)

    # get values for all variables we will need for evaluation
    logger.info('Collecting variables')
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()
    collected_variables = {var: get_variables(sesh, var, ensemble, date_range, region)
                           for var in variables}

    # partially define dict accessor to abstract it for the evaluator
    variable_getter = partial(get_dict_val, collected_variables)

    # evaluate parse trees
    logger.info('Evaluating parse trees')
    result = {id: evaluate_rule(rule, parse_trees, variable_getter)
              for id, rule in parse_trees.items()}

    logger.info('Rules resolved')
    return result
