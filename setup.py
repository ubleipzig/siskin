#!/usr/bin/env python
# coding: utf-8

# Copyright 2015 by Leipzig University Library, http://ub.uni-leipzig.de
#                   The Finc Authors, http://finc.info
#                   Martin Czygan, <martin.czygan@uni-leipzig.de>
#
# This file is part of some open source application.
#
# Some open source application is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# Some open source application is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>

"""
siskin is a set of tasks for library metadata management. For more information
on the project, please refer to https://finc.info.
"""

import sys

from siskin import __version__

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# XXX: Break this up into production and development dependencies.
install_requires = [
    'XlsxWriter>=1.0.2',
    'astroid>=1.1.1,<2',
    'backoff>=1.3.1',
    'bs4',
    'colorama>=0.3.3',
    'configparser>=3.5.0',
    'decorator>=3.4.0',
    'elasticsearch>=2',
    'feedparser>=5.2.1',
    'gluish>=0.3',
    'internetarchive>=1.7.6',
    'iso-639>=0.4.5',
    'langdetect>=1.0.7',
    'logilab-common>=0.61.0',
    'luigi>=2.2',
    'lxml>=3.4.2',
    'marcx>=0.2.10',
    'nose>=1.3.3',
    'numpy',
    'pandas>=0.20.0',
    'pygments>=2',
    'pyisbn>=1.0.0',
    'pymarc>=3.0.1',
    'pymysql>=0.7',
    'python-dateutil>=2.7.5',
    'pytz>=2014.4',
    'rdflib>=4',
    'requests>=2.5.1',
    'responses',
    'six>=1.9.0',
    'tqdm>=4',
    'urllib3>=1.25.10',
    'xlrd>=1.0.0',
    'xmltodict>=0.11.0',
]

if sys.version_info.major < 3:
    install_requires += ['argparse>=1.2', 'wsgiref>=0.1.2']


print("""
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Installation note:

    If you see an error like

    > AttributeError: 'ChangelogAwareDistribution' object has no attribute
      '_egg_fetcher'

    or similar from python-daemon, it's unfortunate but fixable: install
      python-daemon manually, then run setup.py again:

    $ pip install python-daemon
    $ python setup.py develop

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
""")

setup(name='siskin',
      version=__version__,
      description='Luigi tasks for building an article metadata index for https://finc.info',
      url='https://github.com/ubleipzig/siskin',
      author='The Finc Authors',
      author_email='team@finc.info',
      packages=[
          'siskin',
          'siskin.sources',
          'siskin.workflows'
      ],
      package_dir={'siskin': 'siskin'},
      package_data={
          'siskin': [
              'assets/*',
              'assets/arxiv/*',
              'assets/amsl/*',
              'assets/datacite/*',
              'assets/js/*',
              'assets/mail/*',
              'assets/maps/*',
              'assets/oai/*',
              'assets/15/*',
              'assets/20/*',
              'assets/30/*',
              'assets/34/*',
              'assets/39/*',
              'assets/44/*',
              'assets/48/*',
              'assets/52/*',
              'assets/55/*',
              'assets/56_57_58/*',
              'assets/70/*',
              'assets/73/*',
              'assets/78/*',
              'assets/80/*',
              'assets/87/*',
              'assets/88/*',
              'assets/99/*',
              'assets/100/*',
              'assets/101/*',
              'assets/103/*',
              'assets/107/*',
              'assets/109/*',
              'assets/117/*',
              'assets/119/*',
              'assets/124/*',
              'assets/127/*',
              'assets/129/*',
              'assets/130/*',
              'assets/131/*',
              'assets/142/*',
              'assets/143/*',
              'assets/148/*',
              'assets/150/*',
              'assets/151/*',
              'assets/153/*',
              'assets/156/*',
              'assets/160/*',
              'assets/161/*',
              'assets/169/*',
              'assets/170/*',
              'assets/173/*',
              'assets/180/*',
              'assets/181/*',
              'assets/188/*',
          ]},
      scripts=[
          'bin/taskcat',
          'bin/taskchecksetup',
          'bin/taskcleanup',
          'bin/taskconfig',
          'bin/taskdeps',
          'bin/taskdeps-dot',
          'bin/taskdir',
          'bin/taskdo',
          'bin/taskdocs',
          'bin/taskdu',
          'bin/taskgc',
          'bin/taskhash',
          'bin/taskhead',
          'bin/taskhelp',
          'bin/taskhome',
          'bin/taskimportcache',
          'bin/taskinspect',
          'bin/taskless',
          'bin/taskls',
          'bin/tasknames',
          'bin/taskopen',
          'bin/taskoutput',
          'bin/taskps',
          'bin/taskredo',
          'bin/taskrm',
          'bin/taskstatus',
          'bin/tasktags',
          'bin/tasktree',
          'bin/taskversion',
          'bin/taskwc',
          'bin/xmltools.py',
          'bin/solrcheckup.py',
          'bin/siskin-cronjobs',
          'bin/10-fincmarc',
          'bin/14-fincmarc',
          'bin/15-fincmarc',
          'bin/17-fincmarc',
          'bin/20-fincmarc',
          'bin/26-fincmarc',
          'bin/30-fincmarc',
          'bin/35-fincmarc',
          'bin/39-fincmarc',
          'bin/44-fincmarc',
          'bin/52-fincmarc',
          'bin/68-fincjson',
          'bin/70-fincmarc',
          'bin/78-fincmarc',
          'bin/80-fincmarc',
          'bin/88-fincmarc',
          'bin/99-fincmarc',
          'bin/101-fincmarc',
          'bin/109-fincmarc',
          'bin/127-fincmarc',
          'bin/129-fincmarc',
          'bin/142-fincmarc',
          'bin/151-fincmarc',
          'bin/155-fincmarc',
          'bin/159-fincmarc',
          'bin/160-fincmarc',
          'bin/163-fincmarc',
          'bin/169-fincmarc',
          'bin/170-fincmarc',
          'bin/172-fincmarc',
          'bin/180-fincmarc',
          'bin/181-fincmarc',
          'bin/182-fincmarc',
          'bin/183-fincmarc',
          'bin/185-fincmarc',
          'bin/186-fincmarc',
          'bin/187-fincmarc',
          'bin/190-fincmarc',
          'bin/191-fincmarc',
          'bin/192-fincmarc',
          'bin/193-fincmarc',
          'bin/194-fincmarc',
          'bin/195-fincmarc',
          'bin/196-fincmarc',
          'bin/198-fincmarc',
          'bin/199-fincmarc'
      ],
      entry_points={
        'console_scripts': [
            'siskin=siskin.main:main',
        ],
      },
      install_requires=install_requires,
      zip_safe=False,
      classifier=[
          'Development Status :: 4 - Beta',
          'Environment :: Console'
          'License :: GPLv3',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python',
          'Topic :: Text Processing',
      ])
