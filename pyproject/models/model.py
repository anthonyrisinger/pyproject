from . import base
from . import utils


def new(**config):
    object = Model._from_config(config)
    return object


def from_config(config):
    object = Model._from_config(config)
    return object


def from_keyconfig(key, config):
    object = Model._from_keyconfig(key, config)
    return object


class Model(base.BaseModel, model=True):

    pass
