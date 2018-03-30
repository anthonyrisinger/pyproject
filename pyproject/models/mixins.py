import collections
import copy
import json
import urllib.parse

from . import utils


class WithEnviroment:

    _compact_attributes = ['env']
    _attributes = [('env', None)]

    def _env(self, objects=None, escape=None):
        if objects is None:
            objects = [self]
        elif objects is False:
            objects = []

        env = {}
        missing = {}
        envns = utils.envnamespace(self.env)
        for key, value, missed in envns.format_all(objects, escape=escape):
            env[key] = value
            if missed:
                missing[key] = missed

        return env, missing


class WithImage:

    _compact_attributes = ['image']
    _attributes = [('image', ''),
                   ('image_id', None),
                   ('image_registry', None),
                   ('image_project', None),
                   ('image_name', None),
                   ('image_tag', None),
                   ('command', None)]

    @property
    def image(self):
        image = ''
        if self.image_name:
            image += self.image_name
        if self.image_id:
            image += '@sha256:' + self.image_id
        elif self.image_tag:
            image += ':' + self.image_tag
        if self.image_project:
            image = self.image_project + '/' + image
        if self.image_registry:
            image = self.image_registry + '/' + image
        return image

    @image.setter
    def image(self, value):
        if value is None:
            value = '//'

        if not value:
            return

        value = ((2 - value.count('/')) * '/') + value
        registry, project, nametag = value.split('/')
        nametag = nametag + ((1 - nametag.count(':')) * ':')
        name, tag = nametag.split(':')
        if name.endswith('@sha256'):
            id = tag
            tag = None
            name = name[:-7]
        else:
            id = None

        updates = {'image_registry': registry or None,
                   'image_project': project or None,
                   'image_name': name or None,
                   'image_tag': tag or None,
                   'image_id': id or None}
        for key, value in updates.items():
            if value is not None:
                setattr(self, key, value)


class WithUrl:

    _compact_attributes = ['url']
    _attributes = [('url', ''),
                   ('scheme', None),
                   ('username', None),
                   ('password', None),
                   ('hostname', None),
                   ('port', None),
                   ('path', None),
                   ('query', None),
                   ('fragment', None)]

    @utils.attribute
    def query(self, query):
        if isinstance(query, str):
            query = urllib.parse.parse_qsl(query)
        if query is not None:
            query = collections.OrderedDict(query)
            for key, value in query.items():
                try:
                    query[key] = json.loads(value)
                except (ValueError, TypeError):
                    query[key] = value
        return query

    @property
    def hostnames(self):
        hostnames = None
        if self.hostname:
            hostnames = self.hostname.split(',')
        return hostnames

    @hostnames.setter
    def hostnames(self, value):
        if value is not None:
            if not isinstance(value, str):
                value = ','.join(value)
        self.__dict__['hostname'] = value

    @property
    def netloc(self):
        netloc = ''
        if self.username:
            netloc += urllib.parse.quote(self.username, safe='')
        if self.password:
            netloc += ':' + urllib.parse.quote(self.password, safe='')
        if self.hostname:
            if netloc:
                netloc += '@'
            netloc += self.hostname
        if self.port:
            netloc += ':' + str(self.port)
        return netloc

    @netloc.setter
    def netloc(self, value):
        fields = ('username', 'password', 'hostname', 'port')
        if value is None:
            for name in fields:
                setattr(self, name, None)
            return

        url = urllib.parse.urlsplit('//' + value)
        for name in fields:
            output = getattr(url, name)
            if output is not None:
                if name in ('username', 'password'):
                    output = urllib.parse.unquote(output)
                setattr(self, name, output)

    @property
    def url(self):
        netloc = ''
        if self.username:
            netloc += urllib.parse.quote(self.username, safe='')
        if self.password:
            netloc += ':' + urllib.parse.quote(self.password, safe='')
        if self.hostname:
            if netloc:
                netloc += '@'
            netloc += self.hostname
        if self.port:
            netloc += ':' + str(self.port)

        query = self.query or ()
        for key in query:
            value = query[key]
            if not isinstance(value, str):
                value = json.dumps(value)
                query[key] = value
        query = urllib.parse.urlencode(query)

        parts = {'scheme': self.scheme or '',
                 'netloc': netloc,
                 'path': self.path or '',
                 'query': query,
                 'fragment': self.fragment or ''}

        fields = urllib.parse.SplitResult._fields
        url = urllib.parse.SplitResult._make(parts[field] for field in fields)
        return url.geturl()

    @url.setter
    def url(self, value):
        # url is not part of the actual config. It serves as a compact way to
        # configure multiple attributes at once. We want to allow individual
        # overrides to parts of the url, so avoid recording falsey things.
        fields = urllib.parse.SplitResult._fields
        if value is None:
            for name in fields:
                setattr(self, name, None)
            return

        url = urllib.parse.urlsplit(value or '')
        for name in fields:
            output = getattr(url, name) or None
            if output is not None:
                if name in ('username', 'password'):
                    output = urllib.parse.unquote(output)
                setattr(self, name, output)


class WithConnectionUrl(WithUrl):

    _compact_attributes = []
    _attributes = []

    @property
    def database(self):
        database = self.path
        if database is not None:
            database = database.strip('/')
        return database

    @database.setter
    def database(self, value):
        if value is not None:
            value = '/' + value
        setattr(self, 'path', value)


class WithAws:

    _attributes = [('access_key_id', None),
                   ('secret_access_key', None),
                   ('region', None)]
