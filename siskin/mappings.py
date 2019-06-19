# coding: utf-8
# pylint: disable=C0103,W0232,C0301,W0703

# Copyright 2019 by Leipzig University Library, http://ub.uni-leipzig.de
#                   The Finc Authors, http://finc.info
#					Martin Czygan, <martin.czygan@uni-leipzig.de>
#					Robert Schenk, <robert.schenk@uni-leipzig.de>
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
Static mappings for reuse
"""

from collections import defaultdict


formats = defaultdict(dict)

formats[""]["Leader"] = ""
formats[""]["007"] = ""
formats[""]["008"] = ""
formats[""]["336b"] = ""
formats[""]["338b"] = ""
formats[""]["655a"] = ""
formats[""]["6552"] = ""
formats[""]["935c"] = ""
