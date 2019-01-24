# likely that this is where the calls CE backend will live 

import csv
import json

def get_val_from_dict(dict, val):
    return dict[val]


def get_json_var(filename, var):
    data = ''
    with open(filename) as json_data:
        data = json.load(json_data)
    return data[var]


def read_csv(filename):
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
