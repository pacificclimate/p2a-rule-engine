import pytest
from decimal import Decimal
from functools import partial

from p2a_impacts.evaluator import get_symbol_value, cond_operator, evaluate_rule
from p2a_impacts.fetch_data import get_dict_val


@pytest.mark.parametrize(
    ("symbol", "rule_getter", "variable_getter", "expected"),
    [
        ("rule_ten", partial(get_dict_val, {"rule_ten": 10}), None, 10),
        (
            "temp_djf_iamean_s0p_hist",
            None,
            partial(get_dict_val, {"temp_djf_iamean_s0p_hist": -10}),
            -10,
        ),
    ],
)
def test_get_symbol_value(symbol, rule_getter, variable_getter, expected):
    assert expected == get_symbol_value(symbol, rule_getter, variable_getter)


@pytest.mark.parametrize(
    ("symbol", "rules", "variable_getter"),
    [("rule_ten", partial(get_dict_val, {"rule_nine": 9}), None)],
)
def test_get_symbol_value_dict_error_handle(symbol, rules, variable_getter):
    with pytest.raises(KeyError):
        get_symbol_value(symbol, rules, variable_getter)


@pytest.mark.parametrize(
    ("cond", "t_val", "f_val", "expected"), [(True, 1, 0, 1), (False, 1, 0, 0)]
)
def test_cond_operator(cond, t_val, f_val, expected):
    assert expected == cond_operator(cond, t_val, f_val)


@pytest.mark.parametrize(
    ("rule", "rules", "variable_getter", "expected"),
    [
        ((">", 5.01, 6.23), None, None, False),
        (
            ("+", "temp_djf_iamean_s100p_hist", 6.23),
            None,
            partial(get_dict_val, {"temp_djf_iamean_s100p_hist": 20}),
            26.23,
        ),
        (("&&", True, False), None, None, False),
        (("&&", (">", 1, 0), True), None, None, True),
        (("||", True, False), None, None, True),
        (("||", ("<=", 1, 0), False), None, None, False),
        (("?", True, 1, 0), None, None, 1),
        (("!", True), None, None, False),
        (("!", False), None, None, True),
    ],
)
def test_evaluate_rule(rule, rules, variable_getter, expected):
    assert expected == evaluate_rule(rule, rules, variable_getter)


@pytest.mark.parametrize(
    ("rule", "rules", "variable_getter"),
    [
        (("BAD_EXPR", Decimal(5), Decimal(6)), None, None),
    ],
)
def test_evaluate_rule_bad_expression(rule, rules, variable_getter):
    with pytest.raises(NotImplementedError):
        evaluate_rule(rule, rules, variable_getter)
