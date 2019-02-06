import csv
import json
from statistics import mean
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ce.api.models import models
from ce.api.multistats import multistats
from ce.api.multimeta import multimeta


variable_options = {
    'temp': {'min': 'tasmin', 'max': 'tasmax'},
    'prec': 'pr',
    'dg05': 'pr',   # gdd, missing seasonal data
    'nffd': 'fdETCCDI',   # not in 30 year timeseries
    'pass': 'pr',   # this variable is missing from the ensemble?
    'dl18': 'pr'    # hdd, missing seasonal data
}

time_of_year_options = {
    'ann': {'time': '0', 'timescale': 'yearly'},
    'djf': {'time': '0', 'timescale': 'seasonal'},
    'mam': {'time': '1', 'timescale': 'seasonal'},
    'jja': {'time': '2', 'timescale': 'seasonal'},
    'son': {'time': '3', 'timescale': 'seasonal'},
    'jan': {'time': '0', 'timescale': 'monthly'},
    'feb': {'time': '1', 'timescale': 'monthly'},
    'mar': {'time': '2', 'timescale': 'monthly'},
    'apr': {'time': '3', 'timescale': 'monthly'},
    'may': {'time': '4', 'timescale': 'monthly'},
    'jun': {'time': '5', 'timescale': 'monthly'},
    'jul': {'time': '6', 'timescale': 'monthly'},
    'aug': {'time': '7', 'timescale': 'monthly'},
    'sep': {'time': '8', 'timescale': 'monthly'},
    'oct': {'time': '9', 'timescale': 'monthly'},
    'nov': {'time': '10', 'timescale': 'monthly'},
    'dec': {'time': '11', 'timescale': 'monthly'},
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
    """Search through dictionary containing data for different 30 year periods,
       find the desired period and return the target variable.
    """
    try:
        dates = date_options[date_range]
    except KeyError as e:
        print('Bad date range: {}\n{}'.format(date_range, e))
        return None

    for key in periods.keys():
        for date in dates:
            if date in key:
                try:
                    return periods[key][target]
                except KeyError as e:
                    print('Bad target variable: {}\n{}'.format(target, e))
                    return None


def handle_iamean(sesh, model, variable, time_of_year, spatial, date_range, area, percentile):
    """Return the desired variable for a particular climate model"""
    if variable == 'temp':
        tasmin = filter_period_data(spatial_options[spatial], date_range,
                    multistats(sesh,
                        ensemble_name='ce_files',
                        model=model,
                        emission='historical,rcp85',
                        time=time_of_year_options[time_of_year]['time'],
                        area=area,
                        variable=variable_options[variable]['min'],
                        timescale=time_of_year_options[time_of_year]['timescale']))
        tasmax = filter_period_data(spatial_options[spatial], date_range,
                    multistats(sesh,
                        ensemble_name='ce_files',
                        model=model,
                        emission='historical,rcp85',
                        time=time_of_year_options[time_of_year]['time'],
                        area=area,
                        variable=variable_options[variable]['max'],
                        timescale=time_of_year_options[time_of_year]['timescale']))

        try:
            return mean([tasmin, tasmax])
        except KeyError as e:
            print('Unable to get mean of tasmin: {} and tasmax: {}\n{}'
                  .format(tasmin, tasmax, e))
            return None

    else:
        return filter_period_data(spatial_options[spatial], date_range,
            multistats(sesh,
                ensemble_name='ce_files',
                model=model,
                emission='historical,rcp85',
                time=time_of_year_options[time_of_year]['time'],
                area=area,
                variable=variable_options[variable],
                timescale=time_of_year_options[time_of_year]['timescale']))


def get_models(sesh, percentile):
    """Return a list of models needed to compute the percentile"""
    if percentile == 'hist':
        # TODO: return the name of the baseline model
        # this is placeholder code until baseline is determined
        return ['cru_ts_21']
    else:
        return models(sesh, ensemble_name='ce_files')


def get_ce_data(sesh, var_name, date_range, area):
    """Parse a given variable name and into parameters that are used to query
       the Climate Explorer backend.
    """
    try:
        variable, time_of_year, inter_annual_var, \
            spatial, percentile = var_name.split('_')
    except ValueError as e:
        print('Error: Unable to read variable name {}\n{}'.format(var_name, e))
        return None

    models = get_models(sesh, percentile)

    if inter_annual_var == 'iastddev':
        print('Standard Deviation not implemented yet. var_name: {}'.format(var_name))

    elif inter_annual_var == 'iamean':
        result = [
            data for data in [
                handle_iamean(
                    sesh,
                    model,
                    variable,
                    time_of_year,
                    spatial,
                    date_range,
                    area,
                    percentile) for model in models] if data is not None]

        return np.asscalar(np.percentile(result, percentile_options[percentile]))


def get_variables(sesh, var_name, date_range, area):
    """Given a variable name return the value by querying the CE backend"""
    if var_name == 'region_oncoast':
        # TODO: Add /regions endpoint to CE backend for this particular vartiable
        return 1
    else:
        return get_ce_data(sesh, var_name, date_range, area)
