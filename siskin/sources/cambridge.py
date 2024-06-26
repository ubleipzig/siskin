# coding: utf-8
# pylint: disable=C0301,E1101

# Copyright 2018 by Leipzig University Library, http://ub.uni-leipzig.de
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
Cambridge University Press Journals

refs #10167.

Config:

[cambridge]

scp-src = user@ftp.online:/home/cambridge

"""

import datetime
import os

import luigi
from gluish.format import TSV
from gluish.intervals import weekly
from gluish.parameter import ClosestDateParameter
from gluish.utils import shellout

from siskin.common import Executable
from siskin.task import DefaultTask
from siskin.utils import iterfiles


class CambridgeTask(DefaultTask):
    """
    Base task.
    """

    TAG = "133"

    def closest(self):
        return weekly(date=self.date)


class CambridgeDropbox(CambridgeTask):
    """
    Pull down content from FTP dropbox, in Dec '18 about 10K zips.
    """

    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return Executable("rsync", message="https://rsync.samba.org/")

    def run(self):
        target = os.path.join(self.taskdir(), "mirror")
        shellout(
            "mkdir -p {target} && rsync {rsync_options} {src} {target}",
            rsync_options=self.config.get(
                "cambridge", "rsync-options", fallback="-avzP"
            ),
            src=self.config.get("cambridge", "scp-src"),
            target=target,
        )

        if not os.path.exists(self.taskdir()):
            os.makedirs(self.taskdir())

        with self.output().open("w") as output:
            for path in iterfiles(target):
                output.write_tsv(path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="filelist"), format=TSV)
