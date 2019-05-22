import logging
import numpy as np

from ce.api.multistats import multistats

from p2a_impacts.fetch_data import (
    get_models,
    calculate_result,
    filter_by_period,
)


logger = logging.getLogger('scripts')


def query_backend2(
    sesh,
    ensemble_name=None,
    model=None,
    emission=None,
    variable_names=None,
    timescale=None,
    timestep_index=None,
    cell_method=None,
    area=None,
    spatial=None,
    date_ranges=None,
):
    return [
        filter_by_period(
            spatial,
            date_ranges,
            multistats(
                sesh,
                ensemble_name=ensemble_name,
                model=model,
                emission=emission,
                time=timestep_index,
                area=area,
                variable=variable,
                timescale=timescale,
                cell_method=cell_method
            )
        )
        for variable in variable_names
    ]


def statistics(
    sesh,
    ensemble_name=None,
    emission=None,
    variable_names=None,
    timescale=None,
    timestep_index=None,
    temporal=None,
    area=None,
    spatial=None,
    date_ranges=None,
    percentiles=None,
):
    """A simplified version of `get_variables` that does not have to
    munge arguments (much) because we can provide the correct values directly
    as arguments to this function.

    :param sesh: SQLAlchemy database session
        (multistats parameter)

    :param ensemble_name: string specifying CE meta ensemble
        (multistats parameter)
        --> qa['ensemble_name'] --> multistats(ensemble_name)

    :param emission: string specifying CE emission
        (multistats parameter)
        weird computation --> multistats(emission)

    :param variable_names: list of CE short variable names (e.g., 'tasmin')
        (multistats parameter)
        To obtain tasmean, specify ['tasmin', 'tasmax'].
        To obtain nffd (number of frost free days), specify ['fdETCCDI'].
        It is not possible to obtain fdETCCDI.
        For all other variables, specify ['<var name>'].
        --> qa['variable'] --> multistats(variable=v) for v in qa['variable']

    :param timescale: string('yearly'| 'seasonal' | 'monthly') specifying
        CE timescale
        (multistats parameter)
        --> qa['timescale'] --> multistats(timescale)

    :param timestep_index: integer specifying the sub-annual period with
        respect to the timescale (e.g., 0-3 for seasonal)
        (multistats parameter)
        --> qa['time'] --> multistats(time)

    :param temporal: specifies the cell_method (pattern to match?) for selecting
        the dataset file (i.e., searching modelmeta); specifies the temporal
        statistic encoded in the dataset's cell_method
        (multistats parameter)
        --> qa['cell_method'] --> multistats(cell_method)

    :param area: string WKT polygon of selected area
        (multistats parameter)
        --> qa['area'] --> multistats(area)

    :param spatial: string; selects the datum (e.g., mean, min, max) from each
        set of data returned for each file from multistats
        --> qa['spatial'] --> filter_by_period(qa['spatial'], ...)

    :param date_ranges:
        --> qa['dates'] --> filter_by_period(..., qa['dates'], ...)

    :param percentiles: list of float;
        list of across-ensemble percentiles to compute
        --> qa['percentile'] --> np.percentile(results, query_args['percentile'])

    :return: list of float, corresponding to `percentiles`;
        list of computed across-ensemble percentiles

    Example: Compute 25th, 75th percentiles of average summer precipitation
    for historical baseline.

    statistics(
        sesh,
        ensemble_name='p2a_files',
        emission='',        # historical has no emission scenario
        variable_names=['pr'],
        timescale='seasonal',
        timestep_index=2,   # jja
        temporal='mean',    # temporal mean
        spatial='mean',     # spatial mean
        date_ranges=['19710101-20001231'],  # historical baseline
        area='<WKT>',
        percentiles=[25, 75],
    )

    Example: Compute 25th, 75th percentiles of maximum winter precipitation
    for rcp85 emissions scenario in the 2080s.

    statistics(
        sesh,
        ensemble_name='p2a_files',
        emission='',        # historical has no emission scenario
        variable_names=['pr'],
        timescale='seasonal',
        timestep_index=0,   # djf
        temporal='mean',    # temporal mean
        spatial='mean',     # spatial mean
        date_ranges=[       # 2080s
            '20700101-20991231',
            '20710101-21000101',
            '20700101-20991230'
        ],
        area='<WKT>',
        percentiles=[25, 75],
    )

    Example: Compute 10th, 50th, 90th percentiles of annual mean temperature
    for rcp85 emissions scenario in the 2050s.

    statistics(
        sesh,
        ensemble_name='p2a_files',
        emission='historical,rcp85',
        variable_names=['tasmin', 'tasmax'],  # --> tasmean
        timescale='yearly',
        timestep_index=0,
        temporal='mean',    # temporal mean
        spatial='mean',     # spatial mean
        date_ranges=[       # 2050s, several different representations
            '20400101-20691231',
            '20410101-20700101',
            '20400101-20691230'
        ],
        area='<WKT>',
        percentiles=[10, 50, 90],
    )

    Example: Compute 10th, 50th, 90th percentiles of annual mean frost-free days
    for rcp85 emissions scenario in the 2050s.

    statistics(
        sesh,
        ensemble_name='p2a_files',
        emission='historical,rcp85',
        variable_names=['fdETCCDI'],  # --> ffd
        timescale='yearly',
        timestep_index=0,
        temporal='mean',    # temporal mean
        spatial='mean',     # spatial mean
        date_ranges=[       # 2050s, several different representations
            '20400101-20691231',
            '20410101-20700101',
            '20400101-20691230'
        ],
        area='<WKT>',
        percentiles=[10, 50, 90],
    )


    """
    assert ensemble_name is not None
    assert emission is not None
    assert variable_names is not None
    assert timescale is not None
    assert timestep_index is not None
    assert temporal is not None
    assert area is not None  # ??
    assert spatial is not None
    assert date_ranges is not None
    assert percentiles is not None

    logger.info('Collecting models')
    # Here's one place where we have to do reverse argument munging.
    # In `get_models`,
    # the 2nd argument is a value that is 'hist' for the historical baseline
    # dataset, and different from that for projected datasets. This value
    # was derived from a non-obvious combination of the arguments to
    # `get_variables`.
    # Unlike in `get_variables`, here we have direct information about what
    # date ranges have been requested, hence the following:
    historical_baseline_requested = date_ranges == ['19710101-20001231']

    hist_flag = 'hist' if historical_baseline_requested else ''
    models = get_models(sesh, hist_flag, ensemble_name)

    logger.info('Fetching data')
    results = [
        # `calculate_result` takes the raw query results and transforms them
        # into values suitable for consumption by the rules engine. In
        # particular it transforms
        #   tasmin, tasmax --> tasmean
        #   fdETCCDI --> nffd (number of frost free days)
        #   all others --> unchanged
        # TODO: Verify this is appropriate for the Statistics tab data.
        calculate_result(query_data, variable_names, timestep_index, timescale)
        for query_data in [
            query_backend2(
                sesh,
                model,
                ensemble_name,
                variable_names,
                timescale,
                timestep_index,
                temporal,
                area,
                spatial,
                date_ranges,
            ) for model in models
        ]
        # Presumably this means `if None not in query_data`.
        # Which means that results were returned for all models requested.
        if not query_data.count(None)
    ]

    if not results:
        logger.warning('Unable to get data')
        return None
    else:
        return np.percentile(results, percentiles)
