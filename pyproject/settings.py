import re


CONFIG_DIR = 'config'
CONFIG_DIR_MODEL = 'model'

QUALIFIERS = (CONFIG_DIR_MODEL,)

QNAME_SEPARATOR = '/'
QNAME_RE_SEPARATOR = re.escape(QNAME_SEPARATOR)
QNAME_RE_QUALIFIER = '[0-9A-Za-z_]*'
QNAME_RE_NAME = '[0-9A-Za-z_]+'
QNAME_RE = re.compile(f'(?:({QNAME_RE_QUALIFIER})'
                      f'({QNAME_RE_SEPARATOR}))?'
                      f'({QNAME_RE_NAME})')
