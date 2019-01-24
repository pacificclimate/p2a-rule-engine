import csv
import json
import requests
from statistics import mean



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


def get_val_from_keys(stats, value, date):
    for key in stats.keys():
        if date in key:
            return stats[key][value]
    # no match found
    return None


def build_url_params(time, variable, timescale):
    return {'ensemble_name': 'ce_files',  # hard code for now
            'model': 'CanESM2',           # i think the website has a fixed model?
            'emission': 'historical,rcp85',   # fixed??
            'time': time,
            'area': None,                 # this will be determined by website
            'variable': variable,
            'timescale': timescale}


def get_data_from_ce(var_name):
    print(var_name)
    # hard coded for now
    date = '20100101-20391231'

    # lookup tables for known variables
    var_opt = {'temp': {'min': 'tasmin', 'max': 'tasmax'},
               'prec': 'pr'}
    p_opt = {'djf': {'time': 0, 'timescale': 'seasonal'},
             'mam': {'time': 1, 'timescale': 'seasonal'},
             'jja': {'time': 2, 'timescale': 'seasonal'},
             'son': {'time': 3, 'timescale': 'seasonal'},
             'ann': {'time': 0, 'timescale': 'yearly'}}
    val_opt = {'s0p': 'min',
               's100p': 'max',
               'smean': 'mean'}

    # endpoint + api we will use
    request_type = 'multistats'
    url_endpoint = 'https://services.pacificclimate.org/marmot/api/{}'.format(request_type)

    # deconstruct variable name
    var, toy, ia_agg, spat_agg, enstime = var_name.split('_')

    if var == 'prec':
        ret = get_val_from_keys(requests.get(url_endpoint, params=build_url_params(p_opt[toy]['time'], var_opt[var], p_opt[toy]['timescale'])).json(), val_opt[spat_agg], date)
        print(ret)
        return ret
    elif var == 'temp':
        ret = mean([get_val_from_keys(requests.get(url_endpoint, params=build_url_params(p_opt[toy]['time'], var_opt[var]['max'], p_opt[toy]['timescale'])).json(), val_opt[spat_agg], date),
                    get_val_from_keys(requests.get(url_endpoint, params=build_url_params(p_opt[toy]['time'], var_opt[var]['min'], p_opt[toy]['timescale'])).json(), val_opt[spat_agg], date)])
        print(ret)
        return ret
