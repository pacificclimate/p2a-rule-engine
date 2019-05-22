import pytest


@pytest.fixture(scope='function')
def ce_response():
    return {'test_period_20100101-20391230': {'mean': 1, 'min': 0, 'max': 2},
            'test_period_20400101-20691231': {'mean': 3, 'min': 1, 'max': 5},
            'test_period_20700101-20991231': {'mean': 5, 'min': 0, 'max': 10}}
