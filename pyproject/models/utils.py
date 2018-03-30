import json

from ..utils import namespace
from ..utils import qkey
from ..utils import qname


class envnamespace(namespace):

    @classmethod
    def format(cls, value, objects=None, escape=None):
        if objects is None and escape is None:
            # Nothing to do!
            return value

        if not isinstance(value, str):
            value = json.dumps(value)
        elif objects is not None:
            value = value.format(*objects)
        if escape:
            try:
                search, replace = escape
            except ValueError:
                search, replace = escape, escape*2
            value = value.replace(search, replace)

        return value

    def format_all(self, objects=None, escape=None):
        for key, value in self.map.items():
            wrappers = [_envformatwrapper(object, path=[i])
                        for i, object in enumerate(objects)]

            value = self.format(value, objects=wrappers, escape=escape)
            missing = [path for wrapper in wrappers
                            for path in wrapper.missing]

            yield key, value, missing


class _envformatwrapper:

    def __init__(self, object, path=None, root=None, missing=None):
        self.object = object
        self.path = list(map(str, path or [0]))
        self.root = root or self
        if self.root is self:
            if missing is None:
                missing = []
            self.missing = missing

    def __getattr__(self, key):
        path = self.path + [key]
        object = getattr(self.object, key, None)
        wrapper = self.__class__(object, path=path, root=self.root)
        return wrapper

    def __str__(self):
        output = self.object
        if output is None:
           path = '.'.join(self.path)
           self.root.missing.append(path)
           output = '{{{}}}'.format(path)
        elif not isinstance(output, str):
            output = json.dumps(self.object)
        return output


class funproperty:

    def __init__(self, __fun, **kwds):
        self.kwds = namespace(kwds)

        # @defaultproperty
        # def fun(self):
        #     pass
        self(__fun)

    def __call__(self, fun):
        # @defaultproperty(one=1, two=2)
        # def fun(self):
        #     pass
        if fun is not None and not hasattr(fun, '__call__'):
            raise TypeError('not a callable: {}'.format(fun))

        self.name = self.kwds.get('name') or fun.__name__
        self.fun = fun
        return self


class defaultproperty(funproperty):

    def __get__(self, object=None, type=None):
        if object is None:
            return self

        value = self.fun(object)
        return value


class cachingproperty(defaultproperty):

    def __get__(self, object=None, type=None):
        if object is None:
            return self

        cache = object.__dict__[self.name] = super().__get__(object, type)
        return cache


class attribute(funproperty):

    def __get__(self, object, type=None):
        if object is None:
            return self

        output = object.__dict__[self.name]
        return output

    def __set__(self, object, value):
        value = self.fun(object, value, **self.kwds)
        object.__dict__[self.name] = value
