#!/usr/bin/env python
# coding: utf-8
#
# Copyright 2020 by Leipzig University Library, http://ub.uni-leipzig.de
#                   The Finc Authors, http://finc.info
#                   Martin Czygan, <martin.czygan@uni-leipzig.de>
#                   Robert Schenk, <robert.schenk@uni-leipzig.de>
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

Source: Hathi Trust
SID: 35
Ticket: #14511, #15487
Origin: OAI

"""


import re
import os
from io import BytesIO, StringIO

import marcx
import pymarc
from siskin.mappings import formats
from siskin.utils import marc_clean_record, xmlstream
from siskin.arguments import get_arguments, build_inputfilename, build_outputfilename


##################################################################################
# 1. Parse arguments and prepare
##################################################################################

SID = "35"

args = get_arguments()
outputfilename = build_outputfilename(args, SID)
inputfilename = args.inputfilename
outputformat = args.outputformat
filemap = args.filemap

# Set output format for MARC record
if outputformat == "xml":
    outputfile = pymarc.XMLWriter(open(outputfilename, "wb"))
else:
    outputfile = open(outputfilename, "wb")


##################################################################################
# 2. Acquire data
##################################################################################

if not inputfilename:
    inputfilename = build_inputfilename(args, "ndj", SID)
    os.system("metha-sync -set hathitrust:pd https://quod.lib.umich.edu/cgi/o/oai/oai")
    os.system("metha-cat -set hathitrust:pd https://quod.lib.umich.edu/cgi/o/oai/oai > %s" % inputfilename)

lccfile = open(filemap, "r")
lccs = lccfile.readlines()


##################################################################################
# 3. Process data
##################################################################################

for oldrecord in xmlstream(inputfilename, "record"):

    oldrecord = BytesIO(oldrecord)
    oldrecord = pymarc.marcxml.parse_xml_to_array(oldrecord)
    oldrecord = oldrecord[0]

    marcrecord = marcx.Record.from_record(oldrecord)
    marcrecord.force_utf8 = True
    marcrecord.strict = False

    # Leader
    marcrecord.leader = "     " + marcrecord.leader[5:]

    # Identifikator
    f001 = marcrecord["856"]["u"]
    match = re.search(".*\/(.*)", f001)
    if match:
        f001 = match.group(1)
        f001 = f001.replace(".", "")
        marcrecord.remove_fields("001")
        marcrecord.add("001", data="35-" + f001)
    else:
        continue

    # Zugangsfacette
    marcrecord.add("007", data="cr")

    # DDC-Klasse
    marcrecord.remove_fields("082")

    # Profilierung
    try:
        f050a = marcrecord["050"]["a"]
    except:
        continue

    if not f050a:
        continue

    for lcc in lccs:
        lcc = lcc.rstrip("\n")
        match = re.search(lcc, f050a)
        if match:
            break
    else:
        continue

    # Kollektion und Ansigelung
    collections = ["a", f001, "b", "35", "c", u"sid-35-col-hathi"]
    marcrecord.add("980", subfields=collections)

    marc_clean_record(marcrecord)

    if outputformat == "xml":
        outputfile.write(marcrecord)
    else:
        outputfile.write(marcrecord.as_marc())

outputfile.close()
