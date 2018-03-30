import enum


class Proto(enum.Flag):

    O = OWNER = enum.auto()
    I = INSTANCE = enum.auto()
    OI = OWNER_INSTANCE = OWNER | INSTANCE

    G = GET = enum.auto()
    S = SET = enum.auto()
    D = DELETE = enum.auto()
    GSD = GET_SET_DELETE = GET | SET | DELETE

    OG = OWNER_GET = OWNER | GET
    OS = OWNER_SET = OWNER | SET
    OD = OWNER_DELETE = OWNER | DELETE
    IG = INSTANCE_GET = INSTANCE | GET
    IS = INSTANCE_SET = INSTANCE | SET
    ID = INSTANCE_DELETE = INSTANCE | DELETE


class Request:

    @property
    def proto(self):
        return Proto

    def __init__(self, prop=None, instance=None, owner=None, **kwds):
        flags = Proto.OWNER_GET if instance is None else Proto.INSTANCE_GET
        request = self.Request(self, instance, owner)

    def update(self, *args, **kwds):
        updates = {}
        updates.update(*args)
        updates.update(kwds)
        for key in updates:
            setattr(self, key, updates[key])


class config:
    """Configurable property decorator.

    Pass config:
        @prop(name)

    Pass nothing:
        @prop()
        @prop

    Both are handled consistently.
    """

    Request = Request

    def __init__(self, *args, name=None, **kwds):
        """Store decorated function config."""
        self.name = name
        for kv in kwds.items():
            # Push through property (if any) for normalization.
            setattr(self, *kv)
        if args:
            self(*args)

    def __call__(self, fun):
        """Store decorated function."""
        self.fun = fun
        self.name = self.name or fun.__name__
        return self

    def __set_name__(self, owner, name):
        """Prefer name from classdef."""
        self.name = name

    def __get__(self, instance, owner):
        flags = Proto.OWNER_GET if instance is None else Proto.INSTANCE_GET
        request = self.Request(self, instance, owner)
        request.config = self
        value = self.fun(instance, request)
        return value


class caching(config):

    def __init__(self, *args, cache=True, **kwds):
        super().__init__(*args, cache=cache, **kwds)

    def __get__(self, instance, owner):
        cache = self.cache
        value = super().__get__(instance, owner)
        if isinstance(value, self.GET):
            # Value is a marker.
            cache = getattr(value, 'cache', cache)
            value = getattr(value, 'value', value)

        if instance is None:
            # Nowhere to cache things.
            return value

        if cache:
            # Python will stop calling us now.
            instance.__dict__[self.name] = value

        return value


class attribute(caching):

    def __get__(self, instance, owner):
        try:
            value = instance.__dict__[self.name]
        except KeyError:
            try:
                getter = super().__get__
            except AttributeError:
                value = self
            else:
                value = getter(instance, owner)
        return value

    def __set__(self, instance, value):
        request = self.INSTANCE.SET()
        request.config = self
        request.value = value
        value = self.fun(instance, request)
        if value is request:
            value = getattr(value, 'value', value)
        try:
            setter = super().__set__
        except AttributeError:
            pass
        else:
            setter(instance, value)
