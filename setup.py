#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import distutils
import subprocess
from os.path import dirname, join

from setuptools import find_packages, setup


def read(*args, **kwargs):
    return open(join(dirname(__file__), *args), **kwargs).read()


class ToxTestCommand(distutils.cmd.Command):
    """Distutils command to run tests via tox with 'python setup.py test'.

    Please note that in our standard configuration tox uses the dependencies in
    `requirements/dev.txt`, the list of dependencies in `tests_require` in
    `setup.py` is ignored!

    See https://docs.python.org/3/distutils/apiref.html#creating-a-new-distutils-command
    for more documentation on custom distutils commands.
    """
    description = "Run tests via 'tox'."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.announce("Running tests with 'tox'...", level=distutils.log.INFO)
        return subprocess.call(['tox'])


exec(read('planning_poker_jira', 'version.py'))

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Web Environment
Framework :: Django
Framework :: Django :: 3.0
Framework :: Django :: 3.1
Framework :: Django :: 3.2
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: BSD License
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Topic :: Internet
"""

install_requires = [
    'django-searchable-encrypted-fields',
    'jira>=2.0.0',
    'planning-poker',
]

tests_require = [
    'coverage',
    'flake8',
    'pydocstyle',
    'pylint',
    'pytest-django',
    'pytest-cov',
    'pytest-pythonpath',
    'pytest',
]

setup(
    name='planning-poker-jira',
    version=__version__,  # noqa
    description='A jira extension for the planning poker app',
    long_description=read('README.rst', encoding='utf-8'),
    author='Rheinwerk Webteam',
    author_email='webteam@rheinwerk-verlag.de',
    maintainer='Rheinwerk Verlag GmbH Webteam',
    maintainer_email='webteam@rheinwerk-verlag.de',
    url='https://github.com/rheinwerk-verlag/planning-poker-jira',
    license='BSD-3-Clause',
    classifiers=[c.strip() for c in classifiers.splitlines()
                 if c.strip() and not c.startswith('#')],
    packages=find_packages(include=['planning_poker_jira*']),
    include_package_data=True,
    test_suite='tests',
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={
        'test': ToxTestCommand,
    }
)
