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
      version='0.0.8',
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
      # adjust the globs here (http://stackoverflow.com/a/3712682/89391)
      package_data={'siskin': ['assets/*.xsl', 'assets/ambience/*']},
      scripts=[
        'bin/taskcat',
        'bin/taskdo',
        'bin/taskfast',
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
        "backports.ssl-match-hostname==3.4.0.2",
        "colorama==0.3.1",
        "decorator==3.4.0",
        "distribute==0.6.34",
        "elasticsearch==1.0.0",
        "gluish==0.1.55",
        "gspread==0.2.1",
        "jsonpath-rw==1.3.0",
        "logilab-common==0.61.0",
        "luigi==1.0.16",
        "lxml==3.3.5",
        "marcx==0.1.14",
        "nose==1.3.3",
        "numpy==1.8.1",
        "openpyxl==1.8.6",
        "pandas==0.14.0",
        "ply==3.4",
        "prettytable==0.7.2",
        "pyisbn==1.0.0",
        "pylint==1.2.1",
        "pymarc==3.0.1",
        "python-dateutil==2.2",
        "pytz==2014.4",
        "requests==2.3.0",
        "six==1.7.2",
        "sqlitebck==1.2.1",
        "tornado==3.2.2",
        "urllib3==1.8.2",
        "wsgiref==0.1.2",
      ],
)
