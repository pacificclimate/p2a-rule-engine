from argparse import ArgumentParser
from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from resolver import build_parse_tree
from evaluator import evaluate_rule
from data_acquisition import get_val_from_dict, read_csv, get_variables


def main():
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-d', '--date-range', help='30 year period for data',
                        required=True)
    parser.add_argument('-r', '--region', help='Selected region',
                        action='store_true')
    args = parser.parse_args()

    # read csv
    rules = read_csv(args.csv)

    # create parse tree dictionary
    parse_trees = {}
    variables = set()
    for rule, condition in rules.items():
        try:
            parse_trees[rule], vars = build_parse_tree(condition)
        except SyntaxError as e:
            print('{}, rule will be excluded'.format(e))
            continue

        # add unique variables to set
        for var in vars:
            variables.add(var)

    if args.region:
        # use metro vancouver for now
        region = """POLYGON((-122.70904541015625 49.31438004800689,-122.92327880859375
            49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))"""
    else:
        region = None

    # get values for all variables we will need for evaluation
    connection_string = 'postgres://ce_meta_ro@db3.pcic.uvic.ca/ce_meta'
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()
    collected_variables = {var: get_variables(sesh, var, args.date_range, region)
                           for var in variables}

    # partially define dict accessor to abstract it for the evaluator
    variable_getter = partial(get_val_from_dict, collected_variables)

    # evaluate parse trees
    return {id: evaluate_rule(rule, parse_trees, variable_getter)
            for id, rule in parse_trees.items()}


if __name__ == '__main__':
    main()
