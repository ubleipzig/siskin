# coding: utf-8
# pylint: disable=C0301,E1101,C0330,C0111

# Copyright 2023 by Leipzig University Library, http://ub.uni-leipzig.de
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
FOLIO mod-finc-config, mod-finc-select

----

Config:

[folio]

select-url: https://de-15.staging.folio.finc.info/finc-select
config-url: https://de-15.staging.folio.finc.info/finc-config

"""

from siskin.task import DefaultTask


class FolioTask(DefaultTask):
    """
    Base class for FOLIO related tasks
    """

    TAG = "folio"


class FolioSync(FolioTask):
    pass
