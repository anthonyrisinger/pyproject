import collections
import copy
import itertools
import re

from . import errors
from . import utils


class BaseModel:

    _regcache = {}
    _attributes = [('model', None), ('type', None), ('name', 0)]
    _compact_attributes = ['name']
    _key_attributes = ['type', 'name']
    _simple_key = 'type'

    @utils.attribute
    def model(self, value):
        assert value == self._model
        return self._model

    @utils.attribute
    def type(self, value):
        assert value == self._type or (isinstance(value, tuple) and
                                       self._type in value)
        return self._type

    @utils.attribute
    def name(self, value):
        # Strings are global scope and ints are local scope.
        value = str(value) if value else '0'
        if value.isdecimal():
            value = int(value)
        return value

    @property
    def errors(self):
        # This can be used to match any Model related exception.
        #   try: pass
        #   except Model.errors as e: pass
        errs = (errors.CastError,)
        return errs

    @property
    def error(self):
        errs = utils.namespace()
        for err in self.errors:
            errs[err.__name__] = err
        return errs

    @property
    def key(self):
        values = []
        attrs = list(self._attrs('key'))
        for attr in attrs:
            value = getattr(self, attr)
            values.append(value)
        key = utils.qkey(*values)
        return key

    @key.setter
    def key(self, value):
        values = utils.qname(value)
        attrs = list(self._attrs('key'))
        if len(values) == 1 and len(attrs) > 1:
            for key in attrs:
                if key == self._simple_key:
                    # Found simple key. Set and leave.
                    setattr(self, key, values[0])
                    return

        # Expect a complete key at this point.
        while values:
            setattr(self, attrs.pop(), values.pop())

    def __new__(cls, *, model=None, type=None, name=None, **kwds):
        if model is None:
            model = cls._model
        if type is None:
            types = (cls._type,)
        elif isinstance(type, str):
            types = (type,)
        else:
            types = tuple(type)

        # Resolved class we hope to instantiate.
        regcls = None
        for type in types:
            # Search for a suitable model-type.
            try:
                regcls = cls._regcache[model, type]
            except KeyError:
                pass
            else:
                break

        if regcls is None:
            # Failed to locate a matching model-type.
            raise errors.CastError('Bad model-type: {}-{}'.format(model, type))

        if not issubclass(regcls, cls):
            # We are going to raise because we only support proper downcast.
            args = (cls._model, cls._type, regcls._model, regcls._type)
            if issubclass(cls, regcls):
                # regcls is an ancestor of `cls`; no upcasting allowed!
                message = 'Attempted upcast: {}-{} to {}-{}'
            else:
                # Eh?
                message = 'Attempted bad cast: {}-{} to {}-{}: {} to {}'
                args += (cls, regcls)
            message = message.format(*args)
            raise errors.CastError(message)

        if regcls is cls:
            # Nothing special here! Continue up the chain.
            ref = super()
        else:
            # Switching types. Call __new__() from the top.
            ref = regcls

        # Whatever input __new__() received is unconditionally forwarded to
        # __init__() if __new__() returns an instance of the class given or
        # subclass thereof (the typical outcome). __init__()'s signature must
        # always be compatible with the original values sent to __new__().
        self = ref.__new__(regcls)
        return self

    def __init__(self, **kwds):
        # It's important to process attributes in order because some of them
        # are psuedo-config, eg. url -> scheme, hostname, port, etc.
        defaults = collections.OrderedDict(self._attrs())
        # Seed __dict__ with static defaults for all attributes.
        self.__dict__.update(defaults)
        for name, default in defaults.items():
            if name in kwds:
                # setattr will pass the value through any @property filter.
                value = kwds.pop(name)
                setattr(self, name, value)
            else:
                # Try subbing the static default set earlier with a @property.
                value = getattr(self, name, default)
                # Must already be in some preferred form by this point.
                self.__dict__[name] = value

        if kwds:
            # User tried to set something unknown.
            baddies = ', '.join(sorted(kwds))
            message = 'Bad attributes for {}/{}: {}'
            message = message.format(self.model, self.type, baddies)
            raise AttributeError(message)

    def __repr__(self):
        attrs = []
        for name in set(self._attrs('compact')):
            if name not in ('name',):
                value = getattr(self, name)
                if value is not None:
                    if hasattr(value, 'keys'):
                        value = sorted(value.keys())
                        value = '{' + ','.join(value) + '}'
                    value = '{}={}'.format(name, value)
                    attrs.append(value)
        attrs.sort()
        attrs = ' '.join(attrs)
        attrs = ': ' + attrs if attrs else ''
        qualname = '.'.join((self.__class__.__module__,
			     self.__class__.__name__))
        output = '<{}({}){}>'.format(qualname, self.name, attrs)
        return output

    def __len__(self):
        length = len(self.__dict__)
        return length

    def __iter__(self):
        for name in collections.OrderedDict(self._attrs()):
            value = getattr(self, name)
            yield name, value

    def __contains__(self, name):
        if name.startswith('_'):
            contains = False
        elif name in self.__dict__:
            contains = True
        elif hasattr(self.__class__, name):
            contains = True
        else:
            contains = False
        return contains

    def __setitem__(self, name, value):
        try:
            setattr(self, name, value)
        except AttributeError as e:
            raise KeyError(*e.args)

    def __getitem__(self, name):
        try:
            value = getattr(self, name)
            return value
        except AttributeError as e:
            raise KeyError(*e.args)

    def __delitem__(self, name):
        try:
            delattr(self, name)
        except AttributeError as e:
            raise KeyError(*e.args)

    def __setattr__(self, name, value):
        # Leading underscore attrs cannot be model attributes.
        # Pseudo-attributes like `url` are on the class, not in self.__dict__.
        if name.startswith('_') or name in self or hasattr(self.__class__, name):
            # __setattr__ is called before property.__set__, so if this class
            # has a @property in this name, it will be called now.
            super().__setattr__(name, value)
            # self[name] is now in a preferred format.
            return

        raise AttributeError('Bad {} attribute: {}'.format(self.type, name))

    def __delattr__(self, name):
        raise AttributeError('Deleting {} is not allowed.'.format(name))

    def _clone(self):
        # When copying an instance, the copy module will create a new instance
        # and duplicate __dict__. Since we already store finalized attributes
        # in __dict__, and all attributes are either primitives or models,
        # everything works out of the box.
        clone = copy.deepcopy(self)
        return clone

    def _merge_from(self, others, *, nulls=False):
        for other in others:
            self._merge(other, nulls=nulls)
        return self

    def _merge(self, other, *, nulls=False):
        for key, value in other:
            if value is None:
                if nulls:
                    # Value is None and nulls are allowed, reset key.
                    self[key] = None
                continue

            if not hasattr(value, 'items'):
                # Value is simple, overwrite whatever is there.
                self[key] = copy.copy(value)
                continue

            # New value is a dict. Get current-value for comparison.
            current = self[key]

            if not hasattr(current, 'items'):
                # Current-value is simple but new-value is not. Whatever
                # new-value contains... copy all the way down.
                self[key] = copy.deepcopy(value)
                continue

            # Containers on both sides, iterate and merge!
            # {"...": primitive} or {model.key: model}
            for key2, value2 in value.items():
                current2 = current.get(key2)
                # Get the merge function of the current-value.
                merge = getattr(current2, '_merge', None)
                if merge is None:
                    # Get the clone function of the new-value then.
                    clone = getattr(value2, '_clone', None)
                    if clone is None:
                        # No way to copy or overwrite model-style, so just
                        # overwrite normally. Value can be any primitive
                        # [of primitives], but it MUST not contain models
                        # because they will not be merged!
                        value2 = copy.deepcopy(value2)
                        current[key2] = value2
                        continue

                    # Clone the incoming model-value.
                    value2 = clone()
                    current[key2] = value2
                    continue

                # Merge (recurse) with existing model-value.
                value2 = merge(value2)
                current[key2] = value2

            # Pass the value through any normalization.
            self[key] = current

        return self

    def _config(self, attributes=None, **kwds):
        config = {}
        if attributes is None:
            attrs = set(self.__dict__)
        else:
            attrs = set(self._attrs(attributes))

        for key, value in self:
            if key in attrs:
                if hasattr(value, 'items'):
                    value2 = {}
                    for k2, v2 in value.items():
                        if hasattr(v2, '_config'):
                            v2 = v2._config(attributes=attributes, **kwds)
                        value2[k2] = v2
                    value = value2
                if value is not None:
                    config[key] = value

        return config

    @classmethod
    def __init_subclass__(cls, model=None, type=None, **kwds):
        super().__init_subclass__(**kwds)

        # Normalize and guarantee mutable, class-local attributes.
        attributes = list(cls.__dict__.get('_attributes', ()))
        compact_attributes = list(cls.__dict__.get('_compact_attributes', ()))
        auto_compact = False if '_compact_attributes' in cls.__dict__ else True
        for i, attrdef in enumerate(attributes):
            try:
                attr, default = () + attrdef
            except TypeError:
                attr, default = attrdef, None
            attributes[i] = (attr, default)
        if auto_compact and not compact_attributes:
            compact_attributes = [k for k,v in attributes]
        cls._attributes = attributes
        cls._compact_attributes = compact_attributes

        name = re.sub('([A-Z])', r'_\1', cls.__name__).strip('_').lower()
        if model is True:
            # Defines new model using default name.
            model = name
        if type is True or (model and not type):
            # Defines new wildcard type for new or existing model.
            type = '_'
        if not model:
            # Resolves existing model if still not found.
            model = cls._model
        if model and not type:
            # Defines new type using default name.
            type = name

        if model:
            # If model was found, publish it.
            cls._attributes.insert(0, ('model', model))
            cls._model = model
        if type:
            # If type was found, publish it.
            cls._attributes.insert(1, ('type', type))
            cls._type = type

        if model and type:
            # Register this class for the specified model type.
            cls._regcache[model, type] = cls

    @classmethod
    def _attrs(cls, *sections):
        # Generic function to resolve `[_*]_attributes`.
        sections += ('attributes',)
        key = '_' + '_'.join(sections)
        for base in reversed(cls.__mro__):
            attributes = base.__dict__.get(key)
            if attributes is not None:
                yield from attributes

    @classmethod
    def _key_to_config(cls, key):
        values = utils.qname(key)
        attrs = list(cls._attrs('key'))

        if len(values) == 1 and len(attrs) > 1:
            simple = values[0]
            for key in attrs:
                if key == cls._simple_key:
                    # Found simple key. Return simple config.
                    return {key: simple, 'type': (simple, '_')}

        # Expect a complete key at this point.
        config = dict(itertools.zip_longest(attrs, values))
        return config

    @classmethod
    def _from_keyconfig(cls, key, config):
        # Support iterables.
        config = dict(config or ())
        more = cls._key_to_config(key)
        more.update(config)
        dep = cls._from_config(more)
        return dep

    @classmethod
    def _from_config(cls, config):
        # Support iterables.
        config = dict(config)
        dep = cls(**config)
        return dep
