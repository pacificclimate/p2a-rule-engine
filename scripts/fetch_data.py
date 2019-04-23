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
    """Given the number of frost days and a time period determine the number of
       frost free days.
    """
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


def query_backend(sesh, model, query_args):
    """Return the desired variable for a particular climate model"""
    if type(query_args['variable']) is dict:
        tasmin = filter_by_period(query_args['spatial'], query_args['dates'],
                                  multistats(sesh,
                                             ensemble_name=query_args['ensemble_name'],
                                             model=model,
                                             emission=query_args['emission'],
                                             time=query_args['time'],
                                             area=query_args['area'],
                                             variable=query_args['variable']['min'],
                                             timescale=query_args['timescale'],
                                             cell_method=query_args['cell_method']))
        tasmax = filter_by_period(query_args['spatial'], query_args['dates'],
                                  multistats(sesh,
                                             ensemble_name=query_args['ensemble_name'],
                                             model=model,
                                             emission=query_args['emission'],
                                             time=query_args['time'],
                                             area=query_args['area'],
                                             variable=query_args['variable']['max'],
                                             timescale=query_args['timescale'],
                                             cell_method=query_args['cell_method']))
        try:
            return mean([tasmin, tasmax])
        except TypeError as e:
            logger.debug(('Unable to get mean of tasmin: {} and tasmax: {} in '
                          'model: {} error: {}')
                         .format(tasmin, tasmax, model, e))
            return None

    elif query_args['variable'] == 'fdETCCDI':
        fd = filter_by_period(query_args['spatial'], query_args['dates'],
                              multistats(sesh,
                                         ensemble_name=query_args['ensemble_name'],
                                         model=model,
                                         emission=query_args['emission'],
                                         time=query_args['time'],
                                         area=query_args['area'],
                                         variable=query_args['variable'],
                                         timescale=query_args['timescale'],
                                         cell_method=query_args['cell_method']))
        try:
            return get_nffd(fd, query_args['time'], query_args['timescale'])
        except TypeError as e:
            logger.warning('Unable to compute nffd from fd with {} error: {}'
                           .format(fd, e))
            return None

    else:
        return filter_by_period(query_args['spatial'], query_args['dates'],
                                multistats(sesh,
                                           ensemble_name=query_args['ensemble_name'],
                                           model=model,
                                           emission=query_args['emission'],
                                           time=query_args['time'],
                                           area=query_args['area'],
                                           variable=query_args['variable'],
                                           timescale=query_args['timescale'],
                                           cell_method=query_args['cell_method']))


def get_models(sesh, percentile, ensemble):
    """Return a list of models needed to compute the percentile"""
    historical_baseline = 'anusplin'
    if percentile == 'hist':
        return [historical_baseline]
    else:
        # return all models EXCEPT for the historical baseline
        all_models = models(sesh, ensemble_name=query_args['ensemble_name'])
        all_models.remove(historical_baseline)
        return all_models


def translate_variable(variable):
    variables = {
        'temp': {'min': 'tasmin', 'max': 'tasmax'},
        'prec': 'pr',
        'dg05': 'gdd',
        'nffd': 'fdETCCDI',
        'pass': 'prsn',
        'dl18': 'hdd'
    }
    return variables[variable]


def translate_time(time_of_year):
    times = {
        ('ann', 'djf', 'jan'): 0,
        ('mam', 'feb'): 1,
        ('jja', 'mar'): 2,
        ('son', 'apr'): 3,
        ('may'): 4,
        ('jun'): 5,
        ('jul'): 6,
        ('aug'): 7,
        ('sep'): 8,
        ('oct'): 9,
        ('nov'): 10,
        ('dec'): 11
    }
    return next(time for period, time in times.items() if time_of_year in period)


def translate_timescale(time_of_year):
    timescales = {
        ('ann'): 'yearly',
        ('djf', 'mam', 'jja', 'son'): 'seasonal',
        ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
         'jul', 'aug', 'sep', 'oct', 'nov', 'dec'): 'monthly',
    }
    return next(timescale for period, timescale in timescales.items() if time_of_year in period)


def translate_temporal(temporal):
    cell_methods = {
        'iastddev': 'standard_deviation',
        'iamean': 'mean'
    }
    return cell_methods[temporal]


def translate_spatial(spatial):
    spatial_options = {
        's0p': 'min',
        's100p': 'max',
        'smean': 'mean'
    }
    return spatial_options[spatial]


def translate_percentile(percentile):
    percentiles = {
        'e25p': 25,
        'e75p': 75,
        'hist': 100
    }
    return percentiles[percentile]


def translate_emission(percentile, variable):
    emissions = {
        ('temp', 'prec', 'dg05', 'pass', 'dl18'): 'historical,rcp85',
        ('nffd'): 'historical, rcp85',
        ('hist'): ''  # historical has no emission scenario
    }

    if percentile == 'hist':
        emission = percentile
    else:
        emission = variable

    return next(scenario for var, scenario in emissions.items() if emission in var)


def translate_date(percentile, date_range):
    dates = {
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
    }

    if percentile == 'hist':
        period = percentile
    else:
        period = date_range

    return dates[period]


def translate_args(variable, time_of_year, temporal, spatial, percentile, area,
                   date_range, ensemble):
    """Given a set of arguments return a dictionary containing their CE
       counterparts
    """
    return {
        'variable': translate_variable(variable),
        'time': translate_time(time_of_year),
        'timescale': translate_timescale(time_of_year),
        'cell_method': translate_temporal(temporal),
        'spatial': translate_spatial(spatial),
        'percentile': translate_percentile(percentile),
        'emission': translate_emission(percentile, variable),
        'area': area['the_geom'],
        'dates': translate_date(percentile, date_range),
        'ensemble_name': ensemble
    }


def get_ce_data(sesh, var_name, ensemble, date_range, area):
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

    query_args = translate_args(variable, time_of_year, temporal, spatial,
                                percentile, area, date_range, ensemble)
    models = get_models(sesh, percentile, ensemble)

    result = [
        data for data in [query_backend(sesh, model, query_args) for model in models]
        if data is not None
    ]

    return np.asscalar(np.percentile(result, query_args['percentile']))


def get_variables(sesh, var_name, ensemble, date_range, area):
    """Given a variable name return the value by querying the CE backend"""
    if var_name == 'region_oncoast':
        return area['coast_bool'] == '1'
    else:
        return get_ce_data(sesh, var_name, ensemble, date_range, area)
