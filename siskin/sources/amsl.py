# coding: utf-8
# pylint: disable=C0301,E1101,C0330

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
Electronic Resource Management System Based on Linked Data Technologies.

http://amsl.technology

> Managing electronic resources has become a distinctive and important task for
libraries in recent years. The diversity of resources, changing licensing
policies and new business models of the publishers, consortial acquisition and
modern web scale discovery technologies have turned the market place of
scientific information into a complex and multidimensional construct.

Config:

[amsl]

uri-download-prefix = https://x.y.z/OntoWiki/files/get?setResource=
base = https://example.com
fid-issn-list = https://goo.gl/abcdef

"""

from __future__ import print_function

import collections
import datetime
import json
import operator
import tempfile
import zipfile

import luigi

from gluish.format import TSV
from gluish.utils import shellout
from siskin.task import DefaultTask
from siskin.utils import SetEncoder


class AMSLTask(DefaultTask):
    """
    Base class for AMSL related tasks.
    """
    TAG = 'amsl'


class AMSLService(AMSLTask):
    """
    Retrieve AMSL API response. Outbound: discovery, holdingsfiles,
    contentfiles, metadata_usage.

    Example output (discovery):

        [
            {
                "shardLabel": "SLUB-dbod",
                "sourceID": "64",
                "megaCollection": "Perinorm – Datenbank für Normen und technische Regeln",
                "productISIL": null,
                "externalLinkToContentFile": null,
                "contentFileLabel": null,
                "contentFileURI": null,
                "linkToContentFile": null,
                "ISIL": "DE-105",
                "evaluateHoldingsFileForLibrary": "no",
                "holdingsFileLabel": null,
                "holdingsFileURI": null,
                "linkToHoldingsFile": null
            },
            {
                "shardLabel": "SLUB-dbod",
                "sourceID": "64",
                "megaCollection": "Perinorm – Datenbank für Normen und technische Regeln",
                "productISIL": null,
                "externalLinkToContentFile": null,
                "contentFileLabel": null,
                "contentFileURI": null,
                "linkToContentFile": null,
                "ISIL": "DE-14",
                "evaluateHoldingsFileForLibrary": "no",
                "holdingsFileLabel": null,
                "holdingsFileURI": null,
                "linkToHoldingsFile": null
            },
        ...

    """
    date = luigi.DateParameter(default=datetime.date.today())
    name = luigi.Parameter(default='outboundservices:discovery',
                           description='discovery, holdingsfiles, contentfiles, metadata_usage')

    def run(self):
        parts = self.name.split(':')
        if not len(parts) == 2:
            raise RuntimeError('name must be of the form realm:name, e.g. outboundservices:discovery')
        realm, name = parts

        link = '%s/%s/list?do=%s' % (self.config.get('amsl', 'base').rstrip('/'), realm, name)
        output = shellout("""curl --fail "{link}" > {output} """, link=link)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(digest=True))


class AMSLCollectionsShardFilter(AMSLTask):
    """
    A per-shard list of collection entries. One record per line.

        {
          "evaluateHoldingsFileForLibrary": "no",
          "holdingsFileLabel": null,
          "megaCollection": "DOAJ Directory of Open Access Journals",
          "shardLabel": "UBL-ai",
          "contentFileURI": null,
          "sourceID": "28",
          "linkToHoldingsFile": null,
          "holdingsFileURI": null,
          "productISIL": null,
          "linkToContentFile": null,
          "contentFileLabel": null,
          "externalLinkToContentFile": null,
          "ISIL": "DE-14"
        }
        ....

    Shard distribution as of January 2017:

        $ taskcat AMSLService | jq -rc '.[] | .shardLabel' | sort | uniq -c | sort -nr
        53493 UBL-ai
         1121 UBL-main
          245 SLUB-dswarm
           19 SLUB-dbod

    """
    date = luigi.DateParameter(default=datetime.date.today())
    shard = luigi.Parameter(
        default='UBL-ai', description='only collect items for this shard')

    def requires(self):
        return AMSLService(date=self.date, name='outboundservices:discovery')

    def run(self):
        with self.input().open() as handle:
            doc = json.load(handle)

        with self.output().open('w') as output:
            for item in doc:
                if not item['shardLabel'] == self.shard:
                    continue
                output.write(json.dumps(item) + "\n")

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class AMSLCollectionsISILList(AMSLTask):
    """
    A per-shard list of ISILs for which AMSL has some information.

        DE-105
        DE-14
        DE-15
        DE-15-FID
        DE-1972
        DE-540
        ...
    """
    date = luigi.DateParameter(default=datetime.date.today())
    shard = luigi.Parameter(
        default='UBL-ai', description='only collect items for this shard')

    def requires(self):
        return AMSLService(date=self.date, name='outboundservices:discovery')

    def run(self):
        with self.input().open() as handle:
            doc = json.load(handle)

        isils = set()

        for item in doc:
            if not item['shardLabel'] == self.shard:
                continue
            isils.add(item['ISIL'])

        if len(isils) == 0:
            raise RuntimeError('no isils found: maybe mispelled shard name?')

        with self.output().open('w') as output:
            for isil in sorted(isils):
                output.write_tsv(isil)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class AMSLCollectionsISIL(AMSLTask):
    """
    Per ISIL list of collections.

        {
          "48": [
            "Genios (Recht)",
            "Genios (Sozialwissenschaften)",
            "Genios (Psychologie)",
            "Genios (Fachzeitschriften)",
            "Genios (Wirtschaftswissenschaften)"
          ],
          "49": [
            "Helminthological Society (CrossRef)",
            "International Association of Physical Chemists (IAPC) (CrossRef)",
            ...

    Examples (Jan 2017):

        $ taskcat AMSLCollectionsISIL --isil DE-Mit1 --shard SLUB-dbod | jq .
        {
            "64": [
                "Perinorm – Datenbank für Normen und technische Regeln"
            ]
        }

        $ taskcat AMSLCollectionsISIL --isil DE-14 --shard SLUB-dswarm | jq .
        {
            "83": [
                "SLUB/Mediathek"
            ],
            "69": [
                "Wiley ebooks"
            ],
            "105": [
                "Springer Journals"
            ],
            "94": [
                "Blackwell Publishing Journal Backfiles 1879-2005",
                "China Academic Journals (CAJ) Archiv",
                "Wiley InterScience Backfile Collections 1832-2005",
                "Torrossa / Periodici",
                "Cambridge Journals Digital Archive",
                "Elsevier Journal Backfiles on ScienceDirect",
                "Periodicals Archive Online",
                "Emerald Fulltext Archive Database",
                "Springer Online Journal Archives"
            ],
            "67": [
                "SLUB/Deutsche Fotothek"
            ]
        }

        $ taskcat AMSLCollectionsISIL --isil DE-15 --shard SLUB-dswarm | jq .
        {
            "68": [
                "OLC SSG Medien- / Kommunikationswissenschaft",
                "OLC SSG Film / Theater"
            ],
            "94": [
                "Blackwell Publishing Journal Backfiles 1879-2005",
                "China Academic Journals (CAJ) Archiv",
                "Wiley InterScience Backfile Collections 1832-2005",
                "Torrossa / Periodici",
                "Cambridge Journals Digital Archive",
                "Elsevier Journal Backfiles on ScienceDirect",
                "Periodicals Archive Online",
                "Emerald Fulltext Archive Database",
                "Springer Online Journal Archives"
            ],
            "105": [
                "Springer Journals"
            ]
        }
    """
    date = luigi.DateParameter(default=datetime.date.today())
    isil = luigi.Parameter(description='ISIL, case sensitive')
    shard = luigi.Parameter(default='UBL-ai', description='only collect items for this shard')

    def requires(self):
        return AMSLService(date=self.date, name='outboundservices:discovery')

    def run(self):
        with self.input().open() as handle:
            doc = json.load(handle)
        scmap = collections.defaultdict(set)
        for item in doc:
            if not item['shardLabel'] == self.shard:
                continue
            if not item['ISIL'] == self.isil:
                continue
        scmap[item['sourceID']].add(item['megaCollection'].strip())
        if not scmap:
            raise RuntimeError('no collections found for ISIL: %s' % self.isil)

        with self.output().open('w') as output:
            output.write(json.dumps(scmap, cls=SetEncoder) + "\n")

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLHoldingsFile(AMSLTask):
    """
    Access AMSL files/get?setResource= facilities.

    The output is probably zipped (will be decompressed on the fly).

    One ISIL can have multiple files (they will be combined).

    Output should be in standard KBART format, given the uploaded files in AMSL are KBART.
    """
    isil = luigi.Parameter(description='ISIL, case sensitive')
    date = luigi.Parameter(default=datetime.date.today())

    def requires(self):
        return AMSLService(date=self.date, name='outboundservices:holdingsfiles')

    def run(self):
        with self.input().open() as handle:
            holdings = json.load(handle)

        _, stopover = tempfile.mkstemp(prefix='siskin-')

        # The property which contains the URI of the holding file. Might
        # change.
        urikey = 'DokumentURI'

        for holding in holdings:
            if holding["ISIL"] == self.isil:

                if urikey not in holding:
                    raise RuntimeError('possible AMSL API change, expected: %s, available keys: %s' % (
                        urikey, holding.keys()))

                # refs. #7142
                if 'kbart' not in holding[urikey].lower():
                    self.logger.debug(
                        "skipping non-KBART holding URI: %s", holding[urikey])
                    continue

                link = "%s%s" % (self.config.get(
                    'amsl', 'uri-download-prefix'), holding[urikey])
                downloaded = shellout(
                    "curl --fail {link} > {output} ", link=link)
                try:
                    _ = zipfile.ZipFile(downloaded)
                    shellout("unzip -p {input} >> {output}",
                             input=downloaded, output=stopover)
                except zipfile.BadZipfile:
                    # at least the file is not a zip.
                    shellout("cat {input} >> {output}",
                             input=downloaded, output=stopover)

        luigi.LocalTarget(stopover).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLOpenAccessISSNList(AMSLTask):
    """
    List of ISSN, which are open access.

    For now, extract these ISSN from a special holding file, called
    KBART_FREEJOURNALS via AMSL.

    Example (Jan 2017):

        $ taskcat AMSLOpenAccessISSNList | head -10
        0001-0944
        0001-1843
        0001-186X
        0001-1983
        0001-2114
        0001-2211
        0001-267X
        0001-3714
        0001-3757
        0001-3765
    """

    date = luigi.Parameter(default=datetime.date.today())

    def run(self):
        """
        Download, maybe unzip, grab column 2 and 3, keep ISSN, sort -u.
        """
        key = "http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS"
        link = "%s%s" % (self.config.get('amsl', 'uri-download-prefix'), key)

        downloaded = shellout("curl --fail {link} > {output} ", link=link)
        _, stopover = tempfile.mkstemp(prefix='siskin-')

        try:
            _ = zipfile.ZipFile(downloaded)
            output = shellout("unzip -p {input} >> {output}", input=downloaded)
        except zipfile.BadZipfile:
            # at least the file is not a zip.
            output = shellout("cat {input} >> {output}", input=downloaded)

        shellout("cut -f 2 {input} | grep -oE '[0-9]{{4,4}}-[xX0-9]{{4,4}}' >> {output}", input=output, output=stopover)
        shellout("cut -f 3 {input} | grep -oE '[0-9]{{4,4}}-[xX0-9]{{4,4}}' >> {output}", input=output, output=stopover)
        output = shellout("sort -u {input} > {output}", input=stopover)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLFilterConfig(AMSLTask):
    """
    Next version of AMSL filter config.

    Cases:

    61084 Case 3 (ISIL, SID, Collection, Holding File)
      805 Case 2 (ISIL, SID, Collection, Product ISIL)
      380 Case 1 (ISIL, SID, Collection)
       38 Case 4 (ISIL, SID, Collection, External Content File)
       31 Case 6 (ISIL, SID, Collection, External Content File, Holding File)
        1 Case 7 (ISIL, SID, Collection, Internal Content File, Holding File)
        1 Case 5 (ISIL, SID, Collection, Internal Content File)

    Process:

                AMSL Discovery API
                      |
                      v
                AMSLFilterConfig
                      |
                      v
        $ span-tag -c config.json < input.is > output.is

    Notes:

    This task turns an AMSL API response into a filterconfig, which span-tag
    can understand.

    AMSL API might not specify everything we need to know, so this is the
    *only* place, where additional information can be added.

    Also, span-tag is fast, but not that fast, that we can iterate over a
    disjuction of 60000 items fast enough, which, if we could, would simplify
    the implementation of this task.

    The main speed improvement comes from using lists of collection names
    instead of having each collection processed separately - which is how it
    works conceptually: Each collection could use a separate KBART file (or use
    none at all).

    We ignore collection names, if (external) content files are used. These
    content files are usually there, because the data source contains
    collections, which cannot be determined by the datum itself.

    For SID 48 we test simple attachments via DB names parsed from KBART (span
    0.1.144 or later), refs. #10266.

    Performance data point: 22 ISIL each with between 1 and 26 alternatives for
    attachment, each alternative consisting of around three filters. Around 30
    holding or content files each with between 10 and 50000 entries referenced
    220 times in total: around 20k records/s.
    """

    date = luigi.Parameter(default=datetime.date.today())

    def requires(self):
        return AMSLService(date=self.date)

    def run(self):
        with self.input().open() as handle:
            doc = json.loads(handle.read())

        # Case: sid and collection.
        isilsidcollections = collections.defaultdict(
            lambda: collections.defaultdict(set))

        # Case: sid, collection, holding file.
        isilsidfilecollections = collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: collections.defaultdict(set)))

        # Ready-made filters per ISIL:
        isilfilters = collections.defaultdict(list)

        for item in doc:
            if (all(operator.itemgetter('sourceID',
                                        'megaCollection',
                                        'ISIL')(item)) and
                    not any(operator.itemgetter('linkToHoldingsFile',
                                                'linkToContentFile',
                                                'externalLinkToContentFile',
                                                'productISIL')(item))):
                # Case 1 (ISIL, SID, Collection)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    -    -    -     -
                #
                # Group collections by ISIL and SID, combine into:
                # {"and": [{"source": [SID]}, {"collection": [...]}]}

                isilsidcollections[item['ISIL']][item['sourceID']].add(item['megaCollection'])

            elif (all(operator.itemgetter('sourceID',
                                          'megaCollection',
                                          'ISIL',
                                          'productISIL')(item)) and
                    not any(operator.itemgetter('linkToContentFile',
                                                'externalLinkToContentFile')(item))):
                # Case 2 (ISIL, SID, Collection, Product ISIL)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    -    -    -     X

                self.logger.debug("ignoring case with product isil for AI %s, %s, %s", item['ISIL'], item['sourceID'], item['productISIL'])

            elif (all(operator.itemgetter('sourceID',
                                          'megaCollection',
                                          'ISIL',
                                          'linkToHoldingsFile')(item)) and
                    not any(operator.itemgetter('linkToContentFile',
                                                'externalLinkToContentFile',
                                                'productISIL')(item))):
                # Case 3 (ISIL, SID, Collection, Holding File)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    X    -    -     -
                #
                # Group collections by ISIL, SID and holding file, combine into:
                # {"and": [{"source": [SID]}, {"collection": [...]}, {"holdings": {"urls": [...]}}]}

                # Exception: SID 48 should not use collection name, combine into:
                # {"and": [{"source": [SID]}, {"holdings": {"urls": [...]}}]}

                isilsidfilecollections[item['ISIL']][item['sourceID']][item['linkToHoldingsFile']].add(item['megaCollection'])

            elif (all(operator.itemgetter('sourceID',
                                          'megaCollection',
                                          'ISIL',
                                          'externalLinkToContentFile')(item)) and
                    not any(operator.itemgetter('linkToHoldingsFile',
                                                'linkToContentFile',
                                                'productISIL')(item))):
                # Case 4 (ISIL, SID, Collection, External Content File)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    -    -    X     -
                #
                # Create a single item: ISIL, SID, content file:
                # {"and": [{"source": [SID]}, {"holdings": {"urls": [...]}}]}
                #
                # Content files are used, when the raw data does not carry its collection.

                isilfilters[item["ISIL"]].append({
                    "and": [
                        {"source": [item["sourceID"]]},
                        {"holdings": {"urls": [item["externalLinkToContentFile"]]}},
                    ]})

            elif (all(operator.itemgetter('sourceID',
                                          'megaCollection',
                                          'ISIL',
                                          'linkToContentFile')(item)) and
                    not any(operator.itemgetter('linkToHoldingsFile',
                                                'externalLinkToContentFile',
                                                'productISIL')(item))):
                # Case 5 (ISIL, SID, Collection, Internal Content File)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    -    X    -     -
                #
                # Create a single item: ISIL, SID, content file:
                # {"and": [{"source": [SID]}, {"holdings": {"urls": [...]}}]}
                #
                # Content files are used, when the raw data does not carry its collection.

                isilfilters[item["ISIL"]].append({
                    "and": [
                        {"source": [item["sourceID"]]},
                        {"holdings": {"urls": [item["linkToContentFile"]]}},
                    ]})

            elif (all(operator.itemgetter('sourceID',
                                          'megaCollection',
                                          'ISIL',
                                          'linkToHoldingsFile',
                                          'externalLinkToContentFile')(item)) and
                    not any(operator.itemgetter('linkToContentFile',
                                                'productISIL')(item))):
                # Case 6 (ISIL, SID, Collection, External Content File, Holding File)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    X    -    X     -
                #
                # Create a single item: ISIL, SID, content file, holding file:
                # {"and": [{"source": [SID]}, {"holdings": {"urls": [...]}}, {"holdings": {"urls": [...]}}]}
                #
                # First, the content file restricts the set of records, then
                # another holding file can restrict the attachments, e.g. list of
                # ISSN or other.

                isilfilters[item["ISIL"]].append({
                    "and": [
                        {"source": [item["sourceID"]]},
                        {"holdings": {"urls": [item["externalLinkToContentFile"]]}},
                        {"holdings": {"urls": [item["linkToHoldingsFile"]]}},
                    ]})

            elif (all(operator.itemgetter('sourceID',
                                          'megaCollection',
                                          'ISIL',
                                          'linkToHoldingsFile',
                                          'linkToContentFile')(item)) and
                    not any(operator.itemgetter('externalLinkToContentFile',
                                                'productISIL')(item))):
                # Case 7 (ISIL, SID, Collection, Internal Content File, Holding File)
                #
                # SID COLL ISIL LTHF LTCF ELTCF PI
                # --------------------------------
                # X   X    X    X    X    -     -
                #
                # Create a single item: ISIL, SID, content file, holding file:
                # {"and": [{"source": [SID]}, {"holdings": {"urls": [...]}}, {"holdings": {"urls": [...]}}]}
                #
                # First, the content file restricts the set of records, then
                # another holding file can restrict the attachments, e.g. list of
                # ISSN or other.

                isilfilters[item["ISIL"]].append({
                    "and": [
                        {"source": [item["sourceID"]]},
                        {"holdings": {"urls": [item["linkToContentFile"]]}},
                        {"holdings": {"urls": [item["linkToHoldingsFile"]]}},
                    ]})
            else:
                # Bail out, if none of the above cases holds.
                self.logger.debug(item)
                raise RuntimeError("unhandled combination of sid, collection and other parameters")

        # Second pass for some cases.
        for isil, blob in isilsidcollections.items():
            for sid, colls in blob.items():
                if sid == "48":
                    # isilfilters[isil].append({"source": [sid]})
                    self.logger.debug("""suppress single {"source": [48]} filter for %s""", isil)
                    continue
                isilfilters[isil].append({"and": [{"source": [sid]}, {"collection": colls}]})

        for isil, blob in isilsidfilecollections.items():
            for sid, spec in blob.items():
                for link, colls in spec.items():
                    if sid == "48":
                        isilfilters[isil].append({"and": [{"source": [sid]}, {"holdings": {"urls": [link]}}]})
                        continue
                    isilfilters[isil].append({"and": [{"source": [sid]}, {"collection": colls}, {"holdings": {"urls": [link]}}]})

        # Final assembly.
        filterconfig = collections.defaultdict(dict)
        for isil, filters in isilfilters.items():
            if len(filters) == 1:
                filterconfig[isil] = filters[0]
            else:
                filterconfig[isil] = {"or": filters}

        with self.output().open('w') as output:
            json.dump(filterconfig, output, cls=SetEncoder)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='json'))
