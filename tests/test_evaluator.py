import pytest
from decimal import Decimal
from functools import partial

from scripts.evaluator import sub_str_value, cond_operand, \
    evaluate_parse_tree
from scripts.data_acquisition import get_val_from_dict


@pytest.mark.parametrize(('data', 'pt_d', 'variable_getter', 'expected'), [
    ('rule_ten', {'rule_ten': 10}, None, 10),
    ('temp_djf_iamean_s0p_hist', None,
     partial(get_val_from_dict, {'temp_djf_iamean_s0p_hist': -10}), -10)
])
def test_sub_str_value(data, pt_d, variable_getter, expected):
    assert expected == sub_str_value(data, pt_d, variable_getter)


@pytest.mark.parametrize(('data', 'pt_d', 'variable_getter'), [
    ('rule_ten', {'rule_nine': 9}, None)
])
def test_sub_str_value_dict_error_handle(data, pt_d, variable_getter):
    with pytest.raises(KeyError):
        sub_str_value(data, pt_d, variable_getter)


@pytest.mark.parametrize(('cond', 't_val', 'f_val', 'expected'), [
    (True, 1, 0, 1),
    (False, 1, 0, 0)
])
def test_cond_operand(cond, t_val, f_val, expected):
    assert expected == cond_operand(cond, t_val, f_val)


@pytest.mark.parametrize(('pt', 'pt_d', 'variable_getter', 'expected'), [
    (('>', Decimal(5), Decimal(6)), None, None, False),
    (('+', 'temp_djf_iamean_s100p_hist', Decimal(6)), None,
     partial(get_val_from_dict, {'temp_djf_iamean_s100p_hist': 20}), 26),
    (('&&', True, False), None, None, False),
    (('||', True, False), None, None, True),
    (('?', True, 1, 0), None, None, 1),
    (('!', True), None, None, False)
])
def test_evaluate_parse_tree(pt, pt_d, variable_getter, expected):
    assert expected == evaluate_parse_tree(pt, pt_d, variable_getter)
