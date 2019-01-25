import csv
import json
import requests
from statistics import mean


variable_options = {
    'temp': {'min': 'tasmin', 'max': 'tasmax'},
    'prec': 'pr'
}

time_of_year_options = {
    'ann': {'time': 0, 'timescale': 'yearly'},
    'djf': {'time': 0, 'timescale': 'seasonal'},
    'mam': {'time': 1, 'timescale': 'seasonal'},
    'jja': {'time': 2, 'timescale': 'seasonal'},
    'son': {'time': 3, 'timescale': 'seasonal'},
    'jan': {'time': 0, 'timescale': 'monthly'},
    'feb': {'time': 1, 'timescale': 'monthly'},
    'mar': {'time': 2, 'timescale': 'monthly'},
    'apr': {'time': 3, 'timescale': 'monthly'},
    'may': {'time': 4, 'timescale': 'monthly'},
    'jun': {'time': 5, 'timescale': 'monthly'},
    'jul': {'time': 6, 'timescale': 'monthly'},
    'aug': {'time': 7, 'timescale': 'monthly'},
    'sep': {'time': 8, 'timescale': 'monthly'},
    'oct': {'time': 9, 'timescale': 'monthly'},
    'nov': {'time': 10, 'timescale': 'monthly'},
    'dec': {'time': 11, 'timescale': 'monthly'},
}

spat_agg_options = {
    's0p': 'min',
    's100p': 'max',
    'smean': 'mean'
}


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
    """Given dictionary search for a particular date in one of the keys and
       and retrieve the value of the variable at that date.
    """
    for key in stats.keys():
        if date in key:
            return stats[key][value]
    # no match found
    return None


def build_url_params(time, variable, timescale):
    """Add parameters to dictionary representation of query string"""
    return {'ensemble_name': 'ce_files',  # hard code for now
            'model': 'CanESM2',           # i think the website has a fixed model?
            'emission': 'historical,rcp85',   # fixed??
            'time': time,
            'area': None,                 # this will be determined by website
            'variable': variable,
            'timescale': timescale}


def get_ce_data(var_name):
    """Parse a given variable name into parameters that are used to query the
       Climate Explorer backend.
    """
    # hard coded for now
    date = '20100101-20391231'

    # endpoint + api we will use
    request_type = 'multistats'
    url_endpoint = 'https://services.pacificclimate.org/marmot/api/{}'.format(
        request_type)

    # deconstruct variable name
    var, toy, ia_agg, spat_agg, enstime = var_name.split('_')

    if var == 'prec':
        return get_val_from_keys(
            requests.get(
                url_endpoint,
                params=build_url_params(
                    time_of_year_options[toy]['time'],
                    variable_options[var],
                    time_of_year_options[toy]['timescale'])).json(),
            spat_agg_options[spat_agg],
            date)
    elif var == 'temp':
        return mean([
            get_val_from_keys(
                requests.get(
                    url_endpoint,
                    params=build_url_params(
                        time_of_year_options[toy]['time'],
                        variable_options[var]['max'],
                        time_of_year_options[toy]['timescale'])).json(),
                spat_agg_options[spat_agg],
                date),
            get_val_from_keys(
                requests.get(
                    url_endpoint,
                    params=build_url_params(
                        time_of_year_options[toy]['time'],
                        variable_options[var]['min'],
                        time_of_year_options[toy]['timescale'])).json(),
                spat_agg_options[spat_agg],
                date)])


def get_variables(var_name):
    """Given a variable name return the value by lookup table or by querying
       the CE backend.
    """
    if var_name == 'region_oncoast':
        return 1
    else:
        return get_ce_data(var_name)
