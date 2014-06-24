#!/usr/bin/env python
# coding: utf-8

"""
siskin is a set of tasks for library metadata management.
~~~~~~
"""

try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(name='siskin',
      version='0.0.4',
      description='Various sources and workflows.',
      url='https://github.com/miku/siskin',
      author='Martin Czygan',
      author_email='martin.czygan@gmail.com',
      packages=[
        'siskin',
        'siskin.sources',
        'siskin.workflows'
      ],
      package_dir={'siskin': 'siskin'},
      package_data={'siskin': ['assets/*']},
      scripts=[
        'bin/taskcat',
        'bin/taskdo',
        'bin/taskless',
        'bin/taskls',
        'bin/taskman',
        'bin/tasknames',
        'bin/taskoutput',
        'bin/taskredo',
        'bin/taskrm',
        'bin/taskwc',
      ],
      install_requires=[
        "BeautifulSoup==3.2.1",
        "MySQL-python==1.2.5",
        "argparse==1.2.1",
        "astroid==1.1.1",
        "colorama==0.3.1",
        "distribute==0.6.34",
        "elasticsearch==1.0.0",
        "gluish==0.1.52",
        "gspread==0.2.1",
        "logilab-common==0.61.0",
        "luigi==1.0.16",
        "lxml==3.3.5",
        "nose==1.3.3",
        "numpy==1.8.1",
        "openpyxl==1.8.6",
        "pandas==0.14.0",
        "pyisbn==1.0.0",
        "pylint==1.2.1",
        "pymarc==3.0.1",
        "python-dateutil==2.2",
        "pytz==2014.4",
        "requests==2.3.0",
        "six==1.7.2",
        "sqlitebck==1.2.1",
        "urllib3==1.8.2",
        "wsgiref==0.1.2",
      ],
)
