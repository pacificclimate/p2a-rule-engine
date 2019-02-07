import csv
import json
from statistics import mean
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ce.api.models import models
from ce.api.multistats import multistats
from ce.api.multimeta import multimeta


def get_val_from_dict(dict, val):
    """Given a dictionary key name return the associated value"""
    try:
        return dict[val]
    except KeyError as e:
        print('Unable to get val: {} from dict: {}\n{}'.format(val, dict, e))
        return None


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


def filter_period_data(target, dates, periods):
    """Search through dictionary containing data for different 30 year periods,
       find the desired period and return the target variable.
    """
    for key in periods.keys():
        for date in dates:
            if date in key:
                try:
                    return periods[key][target]
                except KeyError as e:
                    print('Bad target variable: {}\n{}'.format(target, e))
                    return None


def query_backend(sesh, model, args):
    """Return the desired variable for a particular climate model"""
    if args['variable'] == 'temp':
        tasmin = filter_period_data(args['spatial'], args['dates'],
                    multistats(sesh,
                        ensemble_name='ce_files',
                        model=model,
                        emission=args['emission'],
                        time=args['time'],
                        area=args['area'],
                        variable=args['variable']['min'],
                        timescale=args['timescale']))
        tasmax = filter_period_data(args['spatial'], args['dates'],
                    multistats(sesh,
                        ensemble_name='ce_files',
                        model=model,
                        emission=args['emission'],
                        time=args['time'],
                        area=args['area'],
                        variable=args['variable']['max'],
                        timescale=args['timescale']))

        try:
            return mean([tasmin, tasmax])
        except KeyError as e:
            print('Unable to get mean of tasmin: {} and tasmax: {}\n{}'
                  .format(tasmin, tasmax, e))
            return None

    else:
        return filter_period_data(args['spatial'], args['dates'],
            multistats(sesh,
                ensemble_name='ce_files',
                model=model,
                emission=args['emission'],
                time=args['time'],
                area=args['area'],
                variable=args['variable'],
                timescale=args['timescale']))


def get_models(sesh, percentile):
    """Return a list of models needed to compute the percentile"""
    if percentile == 'hist':
        # TODO: return the name of the baseline model
        # this is placeholder code until baseline is determined
        return ['cru_ts_21']
    else:
        return models(sesh, ensemble_name='ce_files')


def prep_time_of_year(time_of_year_options, time_of_year):
    try:
        time, timescale = time_of_year_options[time_of_year]
    except KeyError as e:
        print('Bad time of year: {}\n{}'.format(time_of_year, e))
        return None

    return time, timescale


def temp_prep_area(area):
    if area:
        # use metro vancouver for now
        return """POLYGON((-122.70904541015625 49.31438004800689,-122.92327880859375
            49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))"""
    else:
        return None


def prep_args(variable, time_of_year, spatial, percentile, area, date_range):
    variable_options = {
        'temp': {'min': 'tasmin', 'max': 'tasmax'},
        'prec': 'pr',
        'dg05': 'gdd',      # missing seasonal data
        'nffd': 'fdETCCDI', # not in 30 year timeseries
        'pass': None,       # this variable is missing from the ensemble?
        'dl18': 'hdd'       # missing seasonal data
    }
    ce_variable = get_val_from_dict(variable_options, variable)

    spatial_options = {
        's0p': 'min',
        's100p': 'max',
        'smean': 'mean'
    }
    ce_spatial = get_val_from_dict(spatial_options, spatial)

    percentile_options = {
        'e25p': 25,
        'e75p': 75,
        'hist': 100
    }
    ce_percentile = get_val_from_dict(percentile_options, percentile)

    emission_options = {
        'temp': 'historical,rcp85',
        'prec': 'historical,rcp85',
        'dg05': 'historical, rcp85',
        'nffd': 'historical, rcp85',
        'pass': 'historical, rcp85',
        'dl18': 'historical, rcp85'
    }
    ce_emission = get_val_from_dict(emission_options, variable)

    time_of_year_options = {
        'ann': ['0', 'yearly'],
        'djf': ['0', 'seasonal'],
        'mam': ['1', 'seasonal'],
        'jja': ['2', 'seasonal'],
        'son': ['3', 'seasonal'],
        'jan': ['0', 'monthly'],
        'feb': ['1', 'monthly'],
        'mar': ['2', 'monthly'],
        'apr': ['3', 'monthly'],
        'may': ['4', 'monthly'],
        'jun': ['5', 'monthly'],
        'jul': ['6', 'monthly'],
        'aug': ['7', 'monthly'],
        'sep': ['8', 'monthly'],
        'oct': ['9', 'monthly'],
        'nov': ['10', 'monthly'],
        'dec': ['11', 'monthly'],
    }
    ce_time, ce_timescale = prep_time_of_year(time_of_year_options, time_of_year)

    ce_area = temp_prep_area(area)

    date_options = {
        '2020s': ['20100101-20391231', '20110101-20400101', '20100101-20391230'],
        '2050s': ['20400101-20691231'],
        '2080s': ['20700101-20991231']
    }
    dates = get_val_from_dict(date_options, date_range)

    return {'variable': ce_variable,
            'spatial': ce_spatial,
            'percentile': ce_percentile,
            'emission': ce_emission,
            'time': ce_time,
            'timescale': ce_timescale,
            'area': ce_area,
            'dates': dates}


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

    args = prep_args(variable, time_of_year, spatial, percentile,
                     area, date_range)
    models = get_models(sesh, percentile)

    if inter_annual_var == 'iastddev':
        print('Standard Deviation not implemented yet. var_name: {}'.format(var_name))

    elif inter_annual_var == 'iamean':
        result = [
            data for data in [
                query_backend(sesh, model, args) for model in models]
                if data is not None]

        return np.asscalar(np.percentile(result, args['percentile']))


def get_variables(sesh, var_name, date_range, area):
    """Given a variable name return the value by querying the CE backend"""
    if var_name == 'region_oncoast':
        # TODO: Add /regions endpoint to CE backend for this particular vartiable
        return 1
    else:
        return get_ce_data(sesh, var_name, date_range, area)
