from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from .parser import build_parse_tree
from .evaluator import evaluate_rule
from .fetch_data import get_dict_val, read_csv, get_variables


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
    '''Given a range of parameters run the rule engine

       This script controls the flow of the rule engine.  It is responsible for
       calling each of the components (parser, data fetch, evaluator) with the
       correct inputs and handling the outputs.

       NOTES:
           At each stage there is high level error handling that will warn
           the user but continue to finish its task.

           During variable collection the result from the `get_variables(...)`
           call may be None, so we filter those results out.
    '''
    logger = setup_logging(log_level)

    # read csv
    logger.info('Reading {}'.format(csv))
    rules = read_csv(csv)

    # create parse tree dictionary and gather unique variables
    logger.info('Building parse tree')
    parse_trees = {}
    variables = {}
    region_variable = None
    for rule, condition in rules.items():
        try:
            parse_trees[rule], vars, region_var = build_parse_tree(condition)
        except SyntaxError as e:
            logger.warning('{}, rule will be excluded'.format(e))
            continue

        # check region var
        if region_var:
            region_variable = region_var

        # add unique variables to set
        for name, values in vars.items():
            if name not in variables.keys():
                variables[name] = values

    # get values for all variables we will need for evaluation
    logger.info('Collecting variables')
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()

    # gather variable data
    collected_variables = {}
    for name, values in variables.items():
        try:
            var = get_variables(sesh, values, ensemble, date_range, region)
        except Exception as e:
            logger.warning('Error: {} while collecting variable: {}'
                           .format(e, name))
        if var is not None:
            collected_variables[name] = var

    var_count = len(variables)  # count for logger message
    if region_variable:
        var_count += 1
        collected_variables[region_variable] = int(region['coast_bool'])

    logger.info('')
    logger.info('{}/{} variables collected'.format(len(collected_variables),
                                                   var_count))

    # partially define dict accessor to abstract it for the evaluator
    variable_getter = partial(get_dict_val, collected_variables)
    rule_getter = partial(get_dict_val, parse_trees)

    # evaluate parse trees
    logger.info('Evaluating parse trees')
    results = {}
    for id, rule in parse_trees.items():
        try:
            results[id] = evaluate_rule(rule, rule_getter, variable_getter)
        except Exception as e:
            logger.warning('Error {} while resolving {}'.format(e, id))

    logger.info('{}/{} rules resolved'.format(len(results), len(parse_trees)))
    logger.info('Process complete')
    return results
