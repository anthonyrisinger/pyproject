import pytest


def test_casting(Model):
    class NewModel(Model, model=True):
        pass
    class NewType1(NewModel, type='custom_name'):
        pass
    class NewType2(NewModel):
        pass
    model1 = Model(model='new_model', type='custom_name')
    model2 = Model(model='new_model', type='new_type2')
    assert model1.__class__ is NewType1
    assert model2.__class__ is NewType2
    with pytest.raises(model1.error.CastError):
        NewModel(model='model', type='_')
    with pytest.raises(model1.error.CastError):
        NewType1(model='new_model', type='_')

def test_defaults(Model):
    model = Model()
    expect = {'model': 'model',
              'type': '_',
              'name': 0}
    assert expect == model.__dict__
    assert expect == dict(model._attrs())

def test_init(Model):
    model = Model(name=1)
    assert model.__dict__['name'] == 1

def test_bad_init(Model):
    with pytest.raises(AttributeError):
        Model(unknown=None)

def test_bad_setattr(Model):
    model = Model()
    with pytest.raises(AttributeError):
        model.unknown = None

def test_key(Model):
    model = Model()
    assert model.key == '_/0'
    model.name = 1
    assert model.key == '_/1'
    model.name = 'one'
    assert model.key == '_/one'

def test_protocols(Model):
    model = Model()
    # __len__
    assert len(model) == len(dict(model._attrs()))
    # __contains__
    assert 'name' in model
    # __getitem__
    assert model['name'] == 0
    # __getattribute__ (via __dict__ and python runtime)
    assert model.name == 0
    # __setitem__
    model['name'] = 1
    assert model.name == 1
    # __setattr__
    model.name = 0
    assert model.name == 0
    # __delitem__
    with pytest.raises(KeyError):
        del model['name']
    # __delattr__
    with pytest.raises(AttributeError):
        del model.name
    # __iter__
    from collections import OrderedDict
    assert list(model) == list(OrderedDict(model._attrs()).items())

def test_with_url(WithUrlModel):
    model = WithUrlModel(url='')
    assert model.scheme is None
    assert model.username is None
    assert model.password is None
    assert model.hostname is None
    assert model.hostnames is None
    assert model.port is None
    assert model.path is None
    assert model.query is None
    assert model.fragment is None
    assert model.url == ''
    assert model.netloc == ''

    url = 'http://%3A:%3A@one,two:34/app;x?str=wow&int=1234&bool=true#wow'
    model = WithUrlModel(url=url)
    assert model.scheme == 'http'
    assert model.username == ':'
    assert model.password == ':'
    assert model.hostname == 'one,two'
    assert model.hostnames == ['one', 'two']
    assert model.port == 34
    assert model.path == '/app;x'
    assert model.query == {'str': 'wow', 'int': 1234, 'bool': True}
    assert model.fragment == 'wow'
    assert model.url == url
    assert model.netloc == '%3A:%3A@one,two:34'

    # Partial update.
    url = 'http://%3A:%3A@three:56/app;x?str=wow&int=1234&bool=true#wow'
    model.url = '//three:56'
    assert model.url == url
    assert model.netloc == '%3A:%3A@three:56'

    # Drop netloc fields only.
    model.netloc = None
    assert model.scheme == 'http'
    assert model.username == None
    assert model.password == None
    assert model.hostname == None
    assert model.port == None
    assert model.path == '/app;x'
    assert model.netloc == ''

    # Remove all fields.
    model.url = None
    assert model.scheme is None
    assert model.username is None
    assert model.password is None
    assert model.hostname is None
    assert model.hostnames is None
    assert model.port is None
    assert model.path is None
    assert model.query is None
    assert model.fragment is None
    assert model.url == ''
