# This is a setuptools-ism and likely replaced by pyproject.toml in pip 10.0+.

from setuptools import find_packages
from setuptools import setup


name = 'pyproject'
version = '0.1.0'
description = 'Python Project Quick Start.'
long_description = description
author = 'C Anthony Risinger'
author_email = 'c@anthonyrisinger.com'
url = 'https://github.com/anthonyrisinger/pyproject'
classifiers = ['Programming Language :: Python']

install_requires = ['click']
dev_requires = ['IPython']
tests_require = ['pytest']
docs_require = ['sphinx']
extras_require = {'docs': docs_require,
                  'tests': tests_require,
                  'dev': docs_require + tests_require + dev_requires}

entry_points = {'console_scripts': [f'{name} = {name}']}
packages = find_packages(include=[name, f'{name}.*'])


setup(name=name, version=version, author=author, author_email=author_email,
      description=description, long_description=long_description, url=url,
      classifiers=classifiers, packages=packages, entry_points=entry_points,
      install_requires=install_requires, extras_require=extras_require)
