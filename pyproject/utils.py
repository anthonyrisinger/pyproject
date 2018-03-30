from . import settings


def qkey(*qname, separator=settings.QNAME_SEPARATOR):
    qkey = separator.join(map(str, qname))
    return qkey


def qname(qkey, *, separator=settings.QNAME_SEPARATOR):
    qname = tuple(str(qkey).split(separator))
    return qname


def qnames(qnames, *, qualifiers=settings.QUALIFIERS):
    for qname in qnames:
        try:
            q, _, name = settings.QNAME_RE.fullmatch(qname).groups()
        except AttributeError:
            raise ValueError(f'Bad qname: {qname}')

        quals = [qualifier(q, qualifiers=qualifiers)] if q else qualifiers
        if None in quals:
            raise ValueError(f'Bad qname: {qname}')

        for q in quals:
            yield q, name


def qualifier(q, *, qualifiers=settings.QUALIFIERS):
    if not q:
        return

    if q in qualifiers:
        return q

    for qualifier in qualifiers:
        if qualifier.startswith(q):
            return qualifier


class namespace(dict):
    """Dictionary that supports native attribute access"""

    def __new__(cls, *args, **kwds):
        self = super(namespace, cls).__new__(cls, *args, **kwds)
        self.__dict__ = self
        return self
