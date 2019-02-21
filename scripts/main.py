from argparse import ArgumentParser
from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from resolver import build_parse_tree
from evaluator import evaluate_rule
from data_acquisition import get_val_from_dict, read_csv, get_variables


# Logging setup
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)


def main():
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-d', '--date-range', help='30 year period for data',
                        required=True)
    parser.add_argument('-r', '--region', help='Selected region',
                        action='store_true')
    parser.add_argument('-l', '--log-level', help='Logging level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL'],
                        default='INFO')
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.log_level))

    # read csv
    logger.info('Reading {}'.format(args.csv))
    rules = read_csv(args.csv)

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
    connection_string = 'postgres://ce_meta_ro@db3.pcic.uvic.ca/ce_meta'
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()
    collected_variables = {var: get_variables(sesh, var, args.date_range, args.region)
                           for var in variables}

    # partially define dict accessor to abstract it for the evaluator
    variable_getter = partial(get_val_from_dict, collected_variables)

    # evaluate parse trees
    logger.info('Evaluating parse trees')
    result = {id: evaluate_rule(rule, parse_trees, variable_getter)
              for id, rule in parse_trees.items()}

    logger.info('Rules resolved')
    print(result)

if __name__ == '__main__':
    main()
