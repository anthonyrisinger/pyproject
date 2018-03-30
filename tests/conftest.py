
import pytest


@pytest.fixture(scope='session')
def props():
    from pyproject import props
    return props
