import pytest

from scripts.data_acquisition import read_csv, filter_period_data


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


@pytest.mark.parametrize(('target', 'date_range', 'expected'), [
    ('mean', '2020s', 1),
    ('min', '2050s', 1),
    ('max', '2080s', 10)
])
def test_filter_period_data(target, date_range, ce_response, expected):
    assert expected == filter_period_data(target, date_range, ce_response)


@pytest.mark.parametrize(('target', 'date_range'), [
    ('bad_target', '2020s'),
    ('min', 'bad_range')
])
def test_filter_period_data_bad_vars(target, date_range, ce_response):
    assert filter_period_data(target, date_range, ce_response) is None
