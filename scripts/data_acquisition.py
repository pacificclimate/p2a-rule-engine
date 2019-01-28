import csv
import json
import requests
from statistics import mean


variable_options = {
    'temp': {'min': 'tasmin', 'max': 'tasmax'},
    'prec': 'pr',
    'dg05': 'gdd',
    'nffd': 'fdETCCDI',
    # 'pass': '?'
    'dl18': 'hdd'
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

data_options = {
    's0p': 'min',
    's100p': 'max',
    'smean': 'mean'
}

date_options = {
    '2020s': ['20100101-20391231', '20110101-20400101'],
    '2050s': ['20400101-20691231'],
    '2080s': ['20700101-20991231']
}


def get_val_from_dict(dict, val):
    """Given a dictionary key name return the associated value"""
    return dict[val]


def read_csv(filename):
    """Read a csv file which contains at least the id and condition columns
       and return those columns applying a 'rule_' prefix to the id column.
    """
    rules = {}
    with open(filename, 'r') as f:
        csv_reader = list(csv.DictReader(f, delimiter=';'))
        for row in csv_reader:
            rule = 'rule_{}'.format(list(row.values())[0])
            cond = list(row.values())[1]
            rules[rule] = cond

    return rules


def get_period_data(target, date_range, periods):
    """Given a json object containing data for different 30 year periods,
       find the desired period and return the target variable.
    """
    dates = date_options[date_range]
    for key in periods.keys():
        for date in dates:
            if date in key:
                return periods[key][target]

    print('Range {} could not be found in {}'.format(range, periods))
    return None


def request_data(variable, time, timescale):
    """Request data from the Climate Explorer backend using multistats and
       return a json object containing data from all the 30 year periods (2020s,
       2050s, 2080s)
    """
    url = 'https://services.pacificclimate.org/marmot/api/multistats'
    query_string = {
        'ensemble_name': 'ce_files',
        'model': 'CanESM2',             # fixed model?
        'emission': 'historical,rcp85', # fixed emission scenario?
        'time': time,
        'area': None,                   # polygon passed in by p2a?
        'variable': variable,
        'timescale': timescale}

    return requests.get(url, params=query_string).json()


def get_ce_data(var_name, date_range):
    """Parse a given variable name and into parameters that are used to query
       the Climate Explorer backend.
    """
    variable, time_of_year, inter_annual_var, data, percentile = var_name.split('_')

    if variable == 'temp':
        # special case for temp because we have to use tasmin and tasmax together
        tasmin = get_period_data(data_options[data], date_range,
                    request_data(
                        variable_options[variable]['min'],
                        time_of_year_options[time_of_year]['time'],
                        time_of_year_options[time_of_year]['timescale']))
        tasmax = get_period_data(data_options[data], date_range,
                    request_data(
                        variable_options[variable]['max'],
                        time_of_year_options[time_of_year]['time'],
                        time_of_year_options[time_of_year]['timescale']))
        return mean([tasmin, tasmax])

    else:
        return get_period_data(data_options[data], date_range,
                    request_data(
                        variable_options[variable],
                        time_of_year_options[time_of_year]['time'],
                        time_of_year_options[time_of_year]['timescale']))


def get_variables(var_name, date_range):
    """Given a variable name return the value by lookup table or by querying
       the CE backend.
    """
    if var_name == 'region_oncoast':    # temp fix
        return 1
    else:
        return get_ce_data(var_name, date_range)
