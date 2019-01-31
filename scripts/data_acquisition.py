import csv
import json
import requests
from statistics import mean
import numpy as np


variable_options = {
    'temp': {'min': 'tasmin', 'max': 'tasmax'},
    'prec': 'pr',
    'dg05': 'pr',   # gdd, missing seasonal data
    'nffd': 'pr',   # this variable is missing from the ensemble?
    'pass': 'pr',   # this variable is missing from the ensemble?
    'dl18': 'pr'    # hdd, missing seasonal data
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

spatial_options = {
    's0p': 'min',
    's100p': 'max',
    'smean': 'mean'
}

data_options = {
    'iamean': 'mean',
    'iastddev': 'stdev'
}

date_options = {
    '2020s': ['20100101-20391231', '20110101-20400101', '20100101-20391230'],
    '2050s': ['20400101-20691231'],
    '2080s': ['20700101-20991231']
}

percentile_options = {
    'e25p': 25,
    'e75p': 75,
    'hist': 100
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


def filter_period_data(target, date_range, periods):
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


def request_data(model, variable, time, timescale):
    """Request data from the Climate Explorer backend using multistats and
       return a json object containing data from all the 30 year periods (2020s,
       2050s, 2080s)
    """
    url = 'https://services.pacificclimate.org/marmot/api/multistats'
    query_string = {
        'ensemble_name': 'ce_files',
        'model': model,
        'emission': 'historical,rcp85', # fixed emission scenario?
        'time': time,
        'area': None,                   # polygon passed in by front end?
        'variable': variable,
        'timescale': timescale}

    return requests.get(url, params=query_string).json()


def _mean(tasmin, tasmax):
    if tasmin is not None and tasmax is not None:
        return mean([tasmin, tasmax])
    else:
        return None


def handle_iamean(model, variable, time_of_year, spatial, date_range, percentile):
    """Return the desired variable for a particular climate model"""
    if variable == 'temp':
        tasmin = filter_period_data(spatial_options[spatial], date_range,
                    request_data(
                        model,
                        variable_options[variable]['min'],
                        time_of_year_options[time_of_year]['time'],
                        time_of_year_options[time_of_year]['timescale']))
        tasmax = filter_period_data(spatial_options[spatial], date_range,
                    request_data(
                        model,
                        variable_options[variable]['max'],
                        time_of_year_options[time_of_year]['time'],
                        time_of_year_options[time_of_year]['timescale']))

        return _mean(tasmin, tasmax)

    else:
        return filter_period_data(spatial_options[spatial], date_range,
                request_data(
                        model,
                        variable_options[variable],
                        time_of_year_options[time_of_year]['time'],
                        time_of_year_options[time_of_year]['timescale']))


def get_models(percentile):
    """Return a list of models needed to compute the percentile"""
    if percentile == 'hist':
        return ['cru_ts_21']  # baseline
    else:
        url = 'https://services.pacificclimate.org/marmot/api/multimeta'
        query_string = {
            'ensemble_name': 'ce_files'
        }
        meta_data = requests.get(url, params=query_string).json()
        # return a set of all the model ids in the meta data
        return set([meta_data[unique_id]['model_id'] for unique_id in meta_data.keys()])


def get_ce_data(var_name, date_range):
    """Parse a given variable name and into parameters that are used to query
       the Climate Explorer backend.
    """
    try:
        variable, time_of_year, inter_annual_var, \
            spatial, percentile = var_name.split('_')
    except ValueError as e:
        print('Error: Unable to read variable name {}\n{}'.format(var_name, e))
        return None

    models = get_models(percentile)

    if inter_annual_var == 'iastddev':
        # handle this using timeseries???
        print('Standard Deviation not implemented yet. var_name: {}'.format(var_name))

    elif inter_annual_var == 'iamean':
        result = []
        for model in models:
            datum = handle_iamean(model, variable, time_of_year, spatial, date_range, percentile)
            if datum is not None:
                result.append(datum)

        return np.asscalar(np.percentile(result, percentile_options[percentile]))


def get_variables(var_name, date_range):
    """Given a variable name return the value by querying the CE backend"""
    if var_name == 'region_oncoast':
        # TODO: Add /regions endpoint to CE backend for this particular vartiable
        return 1
    else:
        return get_ce_data(var_name, date_range)
