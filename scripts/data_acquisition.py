# likely that this is where the calls CE backend will live

import csv
import json

def get_val_from_dict(dict, val):
    """Given a dictionary key name return the associated value"""
    return dict[val]


def get_json_var(filename, var):
    """Given a variable name return the associated value from a json file"""
    data = ''
    with open(filename) as json_data:
        data = json.load(json_data)
    return data[var]


def read_csv(filename):
    """Read a csv file which contains at least the id and condition columns
       and return those columns applying a 'rule_' prefix to the id column.
    """
    rules_dict = {}
    with open(filename, 'r') as rules_file:
        csv_reader = list(csv.DictReader(rules_file, delimiter=';'))
        for row in csv_reader:
            # make sure we are only getting the id and condition
            # add rule prefix
            rule = 'rule_{}'.format(list(row.values())[0])
            cond = list(row.values())[1]
            rules_dict[rule] = cond

    return rules_dict
