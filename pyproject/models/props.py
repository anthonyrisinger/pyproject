from .. import utils
from .. import props


config = props.config
caching = props.caching
attribute = props.attribute


class modelattribute(props.config):

    def __init__(self, *args, model, collection=True, **kwds):
        model = getattr(model, '_model', model)
        kwds.update(model=model, collection=collection)
        super().__init__(*args, **kwds)

    def __set__(self, instance, value):
        if value is None:
            return

        try:
            value = value.items
        except AttributeError:
            vals = list(value)
        else:
            vals = list(value())

        for i, keyval in enumerate(vals):
            try:
                key, val = () + keyval
            except TypeError:
                key, val = None, keyval
            if getattr(val, 'model', False) == self.model:
                val = val._clone()
            elif key is None:
                val = model.from_config(val)
            else:
                val = model.from_keyconfig(key, val)
            # Replace with reified val.
            vals[i] = val

        vals = utils.namespace((val.key,val) for val in vals)
        defaults = vals.get('_/_')
        if defaults is not None:
            for key, val in vals.items():
                clone = defaults._clone()._merge(val)
                vals[key] = clone
            # Merging in defaults could update the key.
            vals = {val.key: val for val in vals.values()}

        return vals
