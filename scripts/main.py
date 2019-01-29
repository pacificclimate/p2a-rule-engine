from argparse import ArgumentParser
from functools import partial

from resolver import build_parse_tree
from evaluator import evaluate_rule
from data_acquisition import get_val_from_dict, read_csv, get_variables


def print_dict(d):
    """Print out dictionary values in a more human readable format"""
    for key, value in d.items():
        print('Key: {0}\nValue: {1}\n'.format(key, value))


def main():
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-d', '--date-range', help='30 year period for data',
                        required=True)
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

        # add unique variables to set
        for var in vars:
            variables.add(var)

    # get values for all variables we will need for evaluation
    collected_variables = {}
    for var in variables:
        collected_variables[var] = get_variables(var, args.date_range)

    print(collected_variables)

    # partially define dict accessor to abstract it for the evaluator
    variable_getter = partial(get_val_from_dict, collected_variables)

    # evaluate parse trees
    result = {}
    for id, rule in parse_trees.items():
        result[id] = evaluate_rule(rule, parse_trees, variable_getter)

    # print for now
    print_dict(result)


if __name__ == '__main__':
    main()
