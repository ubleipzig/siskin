# coding: utf-8
# pylint: disable=C0301,E1101

# Copyright 2022 by Leipzig University Library, http://ub.uni-leipzig.de
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
Refs. #16327
"""

import datetime
import functools

import requests

import luigi
from gluish.format import Zstd
from gluish.utils import shellout
from siskin.task import DefaultTask


class KalliopeTask(DefaultTask):
    """
    Base task.
    """

    TAG = "140"

    @functools.lru_cache
    def get_last_modified_date(self):
        last_modified_header = requests.head(self.download_url).headers["Last-Modified"]
        last_modified = datetime.datetime.strptime(
            last_modified_header, "%a, %d %b %Y %H:%M:%S %Z"
        )
        return last_modified


class KalliopeDirectDownload(KalliopeTask):
    """
    Download.
    """

    url = luigi.Parameter(
        default="https://download.ubl-proxy.slub-dresden.de/kalliope", significant=False
    )

    def run(self):
        output = shellout(
            """ curl --output {output} --fail -sL "{url}" """,
            url=self.url,
        )
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        last_modified = self.get_last_modified_date()
        filename = "kalliope-{}.tar.gz".format(last_modified.strftime("%Y-%m-%d"))
        return luigi.LocalTarget(path=self.path(filename=filename), format=Gzip)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="ndj.zst"), format=Zstd)
