import pytest

from scripts.fetch_data import read_csv, filter_by_period, prep_args, \
    get_nffd


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
    rules = read_csv('tests/rules-test.csv')
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
def test_filter_by_period(target, dates, ce_response, expected):
    assert expected == filter_by_period(target, dates, ce_response)


@pytest.mark.parametrize(('target', 'dates'), [
    ('bad_target', ['20100101-20391231',
                    '20110101-20400101',
                    '20100101-20391230']),
    ('min', ['bad_dates'])
])
def test_filter_by_period_bad_vars(target, dates, ce_response):
    assert filter_by_period(target, dates, ce_response) is None


@pytest.mark.parametrize(('variable', 'time_of_year', 'cell_method', 'spatial',
                          'percentile', 'area', 'date_range', 'expected'), [
    ('temp', 'djf', 'iamean', 'smean', 'e25p',
     {'the_geom':  """POLYGON((-122.70904541015625 49.31438004800689,
            -122.92327880859375 49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))"""},
     '2020',
     {'variable': {'min': 'tasmin', 'max': 'tasmax'},
      'cell_method': 'mean',
      'spatial': 'mean',
      'percentile': 25,
      'emission': 'historical,rcp85',
      'time': '0',
      'timescale':
      'seasonal',
      'area': """POLYGON((-122.70904541015625 49.31438004800689,
            -122.92327880859375 49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))""",
      'dates': ['20100101-20391231', '20110101-20400101', '20100101-20391230']
      })
])
def test_prep_args(variable, time_of_year, cell_method, spatial, percentile,
        area, date_range, expected): # noqa
    test_args = prep_args(variable, time_of_year, cell_method, spatial,
                          percentile, area, date_range)
    for key in test_args.keys():
        assert test_args[key] == expected[key]


@pytest.mark.parametrize(('fd', 'time', 'timescale', 'expected'), [
    (50, '0', 'seasonal', 39),
    (60, '1', 'seasonal', 32),
    (70, '2', 'seasonal', 22),
    (80, '3', 'seasonal', 11),
    (150, '0', 'yearly', 215)
])
def test_get_nffd(fd, time, timescale, expected):
    assert get_nffd(fd, time, timescale) == expected
