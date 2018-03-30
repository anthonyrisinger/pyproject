import pytest


@pytest.fixture(scope='session')
def Model():
    from pyproject.models.model import Model
    return Model


@pytest.fixture(scope='session')
def WithUrlModel(Model):
    from pyproject.models.mixins import WithUrl
    class WithUrlModel(WithUrl, Model):
        pass
    return WithUrlModel


@pytest.fixture(scope='session')
def WithConnectionUrlModel(Model):
    from pyproject.models.mixins import WithConnectionUrl
    class WithConnectionUrlModel(WithConnectionUrl, Model):
        pass
    return WithConnectionUrlModel
