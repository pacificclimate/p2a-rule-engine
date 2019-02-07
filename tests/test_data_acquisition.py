import pytest

from scripts.data_acquisition import read_csv, filter_period_data, \
    prep_time_of_year, prep_args


@pytest.mark.parametrize(('expected_rules', 'expected_conds'), [
    (['rule_snow', 'rule_hybrid', 'rule_rain', 'rule_future-snow',
      'rule_future-hybrid', 'rule_future-rain'],
     ['(temp_djf_iamean_s0p_hist <= -6)', '((temp_djf_iamean_s0p_hist <= -6)'
      ' && (temp_djf_iamean_s100p_hist >= -6))'
      ' || ((temp_djf_iamean_s0p_hist <= 5) && '
      '(temp_djf_iamean_s100p_hist >= 5)) || ((temp_djf_iamean_s0p_hist >= -6)'
      ' && (temp_djf_iamean_s100p_hist <= 5))',
      '(temp_djf_iamean_s100p_hist >= 5)', '(temp_djf_iamean_s0p_hist + '
      'temp_djf_iamean_s0p_e25p <= -6)', '((temp_djf_iamean_s0p_hist + '
      'temp_djf_iamean_s0p_e25p <= -6) && (temp_djf_iamean_s100p_hist + '
      'temp_djf_iamean_s100p_e75p >= -6)) || ((temp_djf_iamean_s0p_hist + '
      'temp_djf_iamean_s0p_e25p <= 5) && (temp_djf_iamean_s100p_hist + '
      'temp_djf_iamean_s100p_e75p >= 5)) || ((temp_djf_iamean_s0p_hist + '
      'temp_djf_iamean_s0p_e75p >= -6) && (temp_djf_iamean_s100p_hist + '
      'temp_djf_iamean_s100p_e25p <= 5))', '(temp_djf_iamean_s100p_hist + '
      'temp_djf_iamean_s100p_e75p >= 5)'])
])
def test_read_csv(expected_rules, expected_conds):
    rules = read_csv('tests/planners-impacts-test.csv')
    for rule, cond in rules.items():
        assert rule in expected_rules
        assert cond in expected_conds


@pytest.mark.parametrize(('target', 'dates', 'expected'), [
    ('mean', ['20100101-20391231',
              '20110101-20400101',
              '20100101-20391230'], 1),
    ('min', ['20400101-20691231'], 1),
    ('max', ['20700101-20991231'], 10)
])
def test_filter_period_data(target, dates, ce_response, expected):
    assert expected == filter_period_data(target, dates, ce_response)


@pytest.mark.parametrize(('target', 'dates'), [
    ('bad_target', ['20100101-20391231',
                    '20110101-20400101',
                    '20100101-20391230']),
    ('min', ['bad_dates'])
])
def test_filter_period_data_bad_vars(target, dates, ce_response):
    assert filter_period_data(target, dates, ce_response) is None


@pytest.mark.parametrize(('time_of_year_options', 'time_of_year', 'time', 'timescale'), [
    ({'mam': ['1', 'seasonal']}, 'mam', '1', 'seasonal'),
    ({'ann': ['0', 'yearly']}, 'ann', '0', 'yearly'),
    ({'mar': ['2', 'monthly']}, 'mar', '2', 'monthly')
])
def test_prep_time_of_year(time_of_year_options, time_of_year, time, timescale):
    test_time, test_timescale = prep_time_of_year(time_of_year_options, time_of_year)
    assert test_time == time
    assert test_timescale == timescale


@pytest.mark.parametrize(('time_of_year_options', 'time_of_year'), [
    ({'mam': ['1', 'seasonal']}, 'bad_time'),
])
def test_prep_time_of_year_bad_vars(time_of_year_options, time_of_year):
        bad_ret = prep_time_of_year(time_of_year_options, time_of_year)
        assert bad_ret is None


@pytest.mark.parametrize(('variable', 'time_of_year', 'spatial', 'percentile', 'area', 'date_range', 'expected'), [
    ('temp', 'djf', 'smean', 'e25p', True, '2020s',
     {'variable': {'min': 'tasmin', 'max': 'tasmax'},
      'spatial': 'mean',
      'percentile': 25,
      'emission': 'historical,rcp85',
      'time': '0',
      'timescale':
      'seasonal',
      'area': """POLYGON((-122.70904541015625 49.31438004800689,-122.92327880859375
            49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))""",
      'dates': ['20100101-20391231', '20110101-20400101', '20100101-20391230']})
])
def test_prep_args(variable, time_of_year, spatial, percentile, area, date_range, expected):
    test_args = prep_args(variable, time_of_year, spatial, percentile, area, date_range)
    for key in test_args.keys():
        assert test_args[key] == expected[key]
