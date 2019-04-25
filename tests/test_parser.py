import pytest
from decimal import Decimal

from scripts.parser import build_parse_tree


@pytest.mark.parametrize(('rule', 'expected_tree', 'expected_vars'), [
    ('''(test_var_1 > rule_test_1)''', ('>', 'test_var_1', 'rule_test_1'),
     {'test_var_1'}),
    ('''!rule_2b && 5 > 6''',
     ('&&', ('!', 'rule_2b'), ('>', Decimal(5), Decimal(6))), set()),
    ('''rule_3c ? 1:0''', ('?', 'rule_3c', Decimal(1), Decimal(0)), set()),
    ('''(! (1 > 2))''', ('!', ('>', Decimal(1), Decimal(2))), set())
])
def test_build_parse_tree(rule, expected_tree, expected_vars):
    assert expected_tree, expected_vars == build_parse_tree(rule)


@pytest.mark.parametrize(('rule', 'expected'), [
    (['''rule_1a and rule_1b''', '''rule_1a && rule_1b'''],
        ('&&', 'rule_1a', 'rule_1b'))
])
def test_build_parse_tree_error_handle(rule, expected):
    test_output = None
    test_vars = None
    for r in rule:
        try:
            test_output, test_vars, test_region_bool = build_parse_tree(r)
        except SyntaxError as e:
            print('Error has occured: {}'.format(e))
    assert test_output == expected
    assert test_vars == {}
    assert test_region_bool is None
