import pytest
from decimal import Decimal

from scripts.resolver import build_parse_tree


@pytest.mark.parametrize(('data', 'expected_tree', 'expected_vars'), [
    ('''(test_var_1 > rule_test_1)''', ('>', 'test_var_1', 'rule_test_1'),
     {'test_var_1'}),
    ('''!rule_2b && 5 > 6''',
     ('&&', ('!', 'rule_2b'), ('>', Decimal(5), Decimal(6))), set()),
    ('''rule_3c ? 1:0''', ('?', 'rule_3c', Decimal(1), Decimal(0)), set())
])
def test_build_parse_tree(data, expected_tree, expected_vars):
    assert expected_tree, expected_vars == build_parse_tree(data)


@pytest.mark.parametrize(('data', 'expected'), [
    (['''rule_1a and rule_1b''', '''rule_1a && rule_1b'''],
        ('&&', 'rule_1a', 'rule_1b'))
])
def test_build_parse_tree_error_handle(data, expected):
    test_output = None
    test_vars = None
    for rule in data:
        try:
            test_output, test_vars = build_parse_tree(rule)
        except SyntaxError as e:
            print('Error has occured: {}'.format(e))
    assert test_output == expected
    assert test_vars == set()
