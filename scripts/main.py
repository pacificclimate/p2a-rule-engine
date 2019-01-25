from argparse import ArgumentParser
from functools import partial

from resolver import build_parse_tree
from evaluator import evaluate_rule
from data_acquisition import get_val_from_dict, get_json_var, read_csv


def print_dict(d):
    for key, value in d.items():
        print('Key: {0}\nValue: {1}\n'.format(key, value))


def main():
    # I expect this will be reworked into method params
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-f', '--filename', help='JSON file containing data',
                        required=True)
    args = parser.parse_args()

    # read csv
    rules_dict = read_csv(args.csv)

    # create parse tree dictionary
    parse_tree_dict = {}
    variable_set = set()
    for rule, condition in rules_dict.items():
        try:
            parse_tree_dict[rule], vars = build_parse_tree(condition)
        except SyntaxError as e:
            print('{}, rule will be excluded'.format(e))

        # add unique variables to set
        for var in vars:
            variable_set.add(var)

    # get values for all variables we will need for evaluation
    variable_dict = {}
    for var in variable_set:
        variable_dict[var] = get_json_var(args.filename, var)

    # partially define dict accessor to abstract it for the evaluator
    variable_getter = partial(get_val_from_dict, variable_dict)

    # evaluate parse trees
    result_dict = {}
    for rule, pt in parse_tree_dict.items():
        result_dict[rule] = evaluate_rule(pt, parse_tree_dict,
                                                variable_getter)

    # print for now
    print_dict(result_dict)


if __name__ == '__main__':
    main()
