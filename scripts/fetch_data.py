import csv
from statistics import mean
import numpy as np
import logging

from ce.api.models import models
from ce.api.multistats import multistats


logger = logging.getLogger('scripts')


def get_dict_val(dict, val):
    """Given a dictionary key name return the associated value"""
    try:
        return dict[val]
    except KeyError as e:
        logger.warning('Unable to get val: {} from dict: {} error: {}'
                       .format(val, dict, e))
        return None


def read_csv(filename):
    """Read a csv file which contains at least the id and condition columns
       and return those columns applying a 'rule_' prefix to the id column.
    """
    rules = {}
    with open(filename, 'r') as f:
        csv_reader = list(csv.DictReader(f, delimiter=';'))
        rules = {'rule_{}'.format(list(row.values())[0]): list(row.values())[1]
                 for row in csv_reader}

    return rules


def filter_by_period(target, dates, periods):
    """Search through dictionary containing data for different 30 year periods,
       find the desired period and return the target variable.
    """
    for key in periods.keys():
        for date in dates:
            if date in key:
                try:
                    return periods[key][target]
                except KeyError as e:
                    logger.warning('Bad target variable: {} error: {}'
                                   .format(target, e))
                    return None


def get_nffd(fd, time, timescale):
    # TODO: Consider 360 day calendars here?
    if fd is None:
        return None

    if timescale == 'yearly':
        return 365 - fd
    elif timescale == 'seasonal':
        if time == '0':
            return 89 - fd
        elif time == '1' or time == '2':
            return 92 - fd
        elif time == '3':
            return 91 - fd
    else:
        logger.warning(('Could not find matching time for time: {} and '
                        'timescale: {}').format(time, timescale))
        return None


def query_backend(sesh, model, args):
    """Return the desired variable for a particular climate model"""
    if type(args['variable']) is dict:
        tasmin = filter_by_period(args['spatial'], args['dates'],
                                  multistats(sesh,
                                             ensemble_name='p2a_files',
                                             model=model,
                                             emission=args['emission'],
                                             time=args['time'],
                                             area=args['area'],
                                             variable=args['variable']['min'],
                                             timescale=args['timescale'],
                                             cell_method=args['cell_method']))
        tasmax = filter_by_period(args['spatial'], args['dates'],
                                  multistats(sesh,
                                             ensemble_name='p2a_files',
                                             model=model,
                                             emission=args['emission'],
                                             time=args['time'],
                                             area=args['area'],
                                             variable=args['variable']['max'],
                                             timescale=args['timescale'],
                                             cell_method=args['cell_method']))
        try:
            return mean([tasmin, tasmax])
        except TypeError as e:
            logger.debug(('Unable to get mean of tasmin: {} and tasmax: {} in '
                          'model: {} error: {}')
                         .format(tasmin, tasmax, model, e))
            return None

    elif args['variable'] == 'fdETCCDI':
        fd = filter_by_period(args['spatial'], args['dates'],
                              multistats(sesh,
                                         ensemble_name='p2a_files',
                                         model=model,
                                         emission=args['emission'],
                                         time=args['time'],
                                         area=args['area'],
                                         variable=args['variable'],
                                         timescale=args['timescale'],
                                         cell_method=args['cell_method']))
        try:
            return get_nffd(fd, args['time'], args['timescale'])
        except TypeError as e:
            logger.warning('Unable to compute nffd from fd with {} error: {}'
                           .format(fd, e))
            return None

    elif args['percentile'] == 'hist':
        return filter_by_period(args['spatial'], ['19710101-20001231'],
                                multistats(sesh,
                                           ensemble_name='p2a_files',
                                           model=model,
                                           emission=args['emission'],
                                           time=args['time'],
                                           area=args['area'],
                                           variable=args['variable'],
                                           timescale=args['timescale'],
                                           cell_method=args['cell_method']))

    else:
        return filter_by_period(args['spatial'], args['dates'],
                                multistats(sesh,
                                           ensemble_name='p2a_files',
                                           model=model,
                                           emission=args['emission'],
                                           time=args['time'],
                                           area=args['area'],
                                           variable=args['variable'],
                                           timescale=args['timescale'],
                                           cell_method=args['cell_method']))


def get_models(sesh, percentile):
    """Return a list of models needed to compute the percentile"""
    historical_baseline = 'anusplin'
    if percentile == 'hist':
        return [historical_baseline]
    else:
        # return all models EXCEPT for the historical baseline
        all_models = models(sesh, ensemble_name='p2a_files')
        all_models.remove(historical_baseline)
        return all_models


def prep_args(variable, time_of_year, temporal, spatial, percentile, area,
              date_range):
    """Given a set of arguments return a dictionary containing their CE
       counterparts
    """
    args = {}

    ce_variable = {
        'temp': {'min': 'tasmin', 'max': 'tasmax'},
        'prec': 'pr',
        'dg05': 'gdd',
        'nffd': 'fdETCCDI',
        'pass': 'prsn',
        'dl18': 'hdd'
    }[variable]
    args['variable'] = ce_variable

    ce_time, ce_timescale = {
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
    }[time_of_year]
    args['time'] = ce_time
    args['timescale'] = ce_timescale

    ce_cell_method = {
        'iastddev': 'standard_deviation',
        'iamean': 'mean'
    }[temporal]
    args['cell_method'] = ce_cell_method

    ce_spatial = {
        's0p': 'min',
        's100p': 'max',
        'smean': 'mean'
    }[spatial]
    args['spatial'] = ce_spatial

    ce_percentile = {
        'e25p': 25,
        'e75p': 75,
        'hist': 100
    }[percentile]
    args['percentile'] = ce_percentile

    if percentile == 'hist':
        emission = percentile
    else:
        emission = variable
    ce_emission = {
        'temp': 'historical,rcp85',
        'prec': 'historical,rcp85',
        'dg05': 'historical,rcp85',
        'nffd': 'historical, rcp85',
        'pass': 'historical,rcp85',
        'dl18': 'historical,rcp85',
        'hist': ''  # historical has no emission scenario
    }[emission]
    args['emission'] = ce_emission

    args['area'] = area['the_geom']

    if percentile == 'hist':
        dates = percentile
    else:
        dates = date_range
    ce_dates = {
        'hist': ['19710101-20001231'],
        '2020': ['20100101-20391231',
                 '20110101-20400101',
                 '20100101-20391230'],
        '2050': ['20400101-20691231',
                 '20410101-20700101',
                 '20400101-20691230'],
        '2080': ['20700101-20991231',
                 '20710101-21000101',
                 '20700101-20991230']
    }[dates]
    args['dates'] = ce_dates

    return args


def get_ce_data(sesh, var_name, date_range, area):
    """Parse a given variable name and into parameters that are used to query
       the Climate Explorer backend.
    """
    try:
        variable, time_of_year, temporal, \
            spatial, percentile = var_name.split('_')
    except ValueError as e:
        logger.error('Error: Unable to read variable name {} error: {}'
                     .format(var_name, e))
        return None

    args = prep_args(variable, time_of_year, temporal, spatial,
                     percentile, area, date_range)
    models = get_models(sesh, percentile)

    result = [
        data for data in [query_backend(sesh, model, args) for model in models]
        if data is not None
    ]

    return np.asscalar(np.percentile(result, args['percentile']))


def get_variables(sesh, var_name, date_range, area):
    """Given a variable name return the value by querying the CE backend"""
    if var_name == 'region_oncoast':
        return area['coast_bool'] == '1'
    else:
        return get_ce_data(sesh, var_name, date_range, area)
