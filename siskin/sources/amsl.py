# coding: utf-8
# pylint: disable=C0301,E1101,C0330,C0111

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

https://amsl.technology

> Managing electronic resources has become a distinctive and important task for
libraries in recent years. The diversity of resources, changing licensing
policies and new business models of the publishers, consortial acquisition and
modern web scale discovery technologies have turned the market place of
scientific information into a complex and multidimensional construct.

These tasks wrap API responses, allow access to holding files, and create a
filterconfig which can be use fed into
[span-tag](https://github.com/miku/span/tree/master/cmd/span-tag).

----

TODO: migrate to FOLIO API.

----

TODO: #14841 jstor names

    $ taskcat AMSLService | jq -r '.[] | select(.sourceID == "55") | [.technicalCollectionID, .megaCollection] | @tsv' | sort -u

----

Config:

[amsl]

base = https://x.y.z
uri-download-prefix = https://x.y.z/OntoWiki/files/get?setResource=
write-url = https://x.y.z/OntoWiki/x/y # For time-stamping.

"""

from __future__ import print_function

import collections
import datetime
import gzip
import json
import operator
import tempfile
import zipfile

import luigi
from gluish.format import TSV, Gzip
from gluish.utils import shellout

from siskin.task import DefaultTask
from siskin.utils import SetEncoder, dictcheck


class AMSLTask(DefaultTask):
    """
    Base class for AMSL related tasks.
    """

    TAG = "amsl"


class AMSLServiceDeprecated(AMSLTask):
    """
    Defunkt task via #14415 as of 2018-12-12. Will be remove soon.

    Retrieve AMSL API response. Outbound: holdingsfiles, contentfiles, metadata_usage.
    2018-12-12: discovery API EOL, XXX: adjust, refs #14415.

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
    name = luigi.Parameter(
        default="outboundservices:discovery",
        description="discovery, holdingsfiles, contentfiles, metadata_usage, freeContent",
    )

    def run(self):
        parts = self.name.split(":")
        if not len(parts) == 2:
            raise RuntimeError("realm:name expected, e.g. outboundservices:discovery")
        realm, name = parts

        link = "%s/%s/list?do=%s" % (
            self.config.get("amsl", "base").rstrip("/"),
            realm,
            name,
        )
        output = shellout("""curl --fail "{link}" | pigz -c > {output} """, link=link)

        # Check for valid JSON before, simplifies debugging.
        with gzip.open(output, "rb") as handle:
            try:
                _ = json.load(handle)
            except ValueError:
                self.logger.warning("AMSL API did not return valid JSON")
                raise

        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(
            path=self.path(digest=True, ext="json.gz"), format=Gzip
        )


class AMSLService(AMSLTask):
    """
    Approximation of discovery response until better approach is implemented. Requires span 0.1.273 or later.
    """

    date = luigi.DateParameter(default=datetime.date.today())
    name = luigi.Parameter(
        default="outboundservices:discovery",
        description="ignored, kept for compatibility",
    )

    def requires(self):
        if self.name != "outboundservices:discovery":
            return AMSLServiceDeprecated(date=self.date, name=self.name)
        return []

    def run(self):
        if self.name == "outboundservices:discovery":
            output = shellout(
                "span-amsl-discovery -live {live} | gzip -c > {output}",
                live=self.config.get("amsl", "base"),
            )
        else:
            output = self.input().path

        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(
            path=self.path(digest=True, ext="json.gz"), format=Gzip
        )


class AMSLServiceTab(AMSLTask):
    """
    Turn API response into TSV.
    """

    date = luigi.DateParameter(default=datetime.date.today())
    name = luigi.Parameter(
        default="outboundservices:discovery",
        description="ignored, kept for compatibility",
    )

    def requires(self):
        if self.name != "outboundservices:discovery":
            return AMSLServiceDeprecated(date=self.date, name=self.name)
        return []

    def run(self):
        if self.name == "outboundservices:discovery":
            output = shellout(
                "span-amsl-discovery -f -live {live} | pigz -c > {output}",
                live=self.config.get("amsl", "base"),
            )
        else:
            output = self.input().path

        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(digest=True, ext="tsv.gz"), format=Gzip)


class AMSLCollections(AMSLTask):
    """
    Report all collections, that appear in AMSL.
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return AMSLService(date=self.date, name="outboundservices:discovery")

    def run(self):
        output = shellout(
            """ unpigz -c {input} | jq -rc '.[]|.megaCollection' | sort -u > {output}""",
            input=self.input().path,
        )
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


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
        default="UBL-ai", description="only collect items for this shard"
    )

    def requires(self):
        return AMSLService(date=self.date, name="outboundservices:discovery")

    def run(self):
        with self.input().open() as handle:
            doc = json.load(handle)

        with self.output().open("w") as output:
            for item in doc:
                if not item["shardLabel"] == self.shard:
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
        FID-MEDIEN-DE-15
        DE-1972
        DE-540
        ...
    """

    date = luigi.DateParameter(default=datetime.date.today())
    shard = luigi.Parameter(
        default="UBL-ai", description="only collect items for this shard"
    )

    def requires(self):
        return AMSLService(date=self.date, name="outboundservices:discovery")

    def run(self):
        with self.input().open() as handle:
            doc = json.load(handle)

        isils = set()

        for item in doc:
            if not item["shardLabel"] == self.shard:
                continue
            isils.add(item["ISIL"])

        if len(isils) == 0:
            raise RuntimeError("no isils found: maybe mispelled shard name?")

        with self.output().open("w") as output:
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
    isil = luigi.Parameter(default="DE-15", description="ISIL, case sensitive")
    shard = luigi.Parameter(
        default="UBL-ai", description="only collect items for this shard"
    )

    def requires(self):
        return AMSLService(date=self.date, name="outboundservices:discovery")

    def run(self):
        with self.input().open() as handle:
            doc = json.load(handle)

        unique_shards = set()

        scmap = collections.defaultdict(set)
        for item in doc:
            unique_shards.add(item["shardLabel"])
            if not item["shardLabel"] == self.shard:
                continue
            if not item["ISIL"] == self.isil:
                continue
            scmap[item["sourceID"]].add(item["megaCollection"].strip())
            if not scmap:
                raise RuntimeError("no collections found for ISIL: %s" % self.isil)

        if not scmap and self.shard not in unique_shards:
            self.logger.warn("available shards: %s", list(unique_shards))

        with self.output().open("w") as output:
            output.write(json.dumps(scmap, cls=SetEncoder) + "\n")

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLHoldingsFile(AMSLTask):
    """
    Access AMSL files/get?setResource= facilities.

    The output is probably zipped (will be decompressed on the fly).

    One ISIL can have multiple files (they will be concatenated).

    Output should be in standard KBART format, given the uploaded files in AMSL are KBART.
    """

    isil = luigi.Parameter(default="DE-15", description="ISIL, case sensitive")
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return AMSLService(date=self.date, name="outboundservices:holdingsfiles")

    def run(self):
        with self.input().open() as handle:
            holdings = json.load(handle)

        _, stopover = tempfile.mkstemp(prefix="siskin-")

        # The property containing the URI of the holding file, maybe.
        urikey = "DokumentURI"

        for holding in holdings:
            if holding["ISIL"] == self.isil:
                if urikey not in holding:
                    raise RuntimeError(
                        "possible AMSL API change, expected: %s, available keys: %s"
                        % (urikey, list(holding.keys()))
                    )

                # refs. #7142
                if "kbart" not in holding[urikey].lower():
                    self.logger.debug(
                        "skipping non-KBART holding URI: %s", holding[urikey]
                    )
                    continue

                link = "%s%s" % (
                    self.config.get("amsl", "uri-download-prefix"),
                    holding[urikey],
                )
                downloaded = shellout("curl --fail {link} > {output} ", link=link)
                try:
                    _ = zipfile.ZipFile(downloaded)
                    shellout(
                        "unzip -p {input} >> {output}",
                        input=downloaded,
                        output=stopover,
                    )
                except zipfile.BadZipfile:
                    # Probably not a zip.
                    shellout(
                        "cat {input} >> {output}", input=downloaded, output=stopover
                    )

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

    As of October 2017, this list includes: https://pub.uni-bielefeld.de/download/2913654/2913655.
    As of December 2018, there are 72692 ISSN listed.
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def run(self):
        """
        Download, maybe unzip, grab column 2 and 3, keep ISSN, sort -u.
        """
        key = "http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS"
        link = "%s%s" % (self.config.get("amsl", "uri-download-prefix"), key)

        downloaded = shellout("curl --fail {link} > {output} ", link=link)
        _, stopover = tempfile.mkstemp(prefix="siskin-")

        try:
            _ = zipfile.ZipFile(downloaded)
            output = shellout("unzip -p {input} >> {output}", input=downloaded)
        except zipfile.BadZipfile:
            # At least the file is not a zip.
            output = shellout("cat {input} >> {output}", input=downloaded)

        shellout(
            "cut -f 2 {input} | grep -oE '[0-9]{{4,4}}-[xX0-9]{{4,4}}' >> {output}",
            input=output,
            output=stopover,
        )
        shellout(
            "cut -f 3 {input} | grep -oE '[0-9]{{4,4}}-[xX0-9]{{4,4}}' >> {output}",
            input=output,
            output=stopover,
        )

        # Include OA list, refs #11579, maybe cache this?
        shellout(
            """curl -s https://pub.uni-bielefeld.de/download/2913654/2913655 | cut -d, -f1,2 | tr -d '"' |
                    grep -E '[0-9]{{4,4}}-[0-9]{{3,3}}[0-9xX]' | tr ',' '\n' >> {output}""",
            output=stopover,
            preserve_whitespace=True,
        )

        output = shellout("sort -u {input} > {output}", input=stopover)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLGoldListKBART(AMSLTask):
    """
    Convert Bielefeld Gold List to KBART (for manual uploads in AMSL). As of
    December 2018, there are 36706 ISSN in this list.
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def run(self):
        _, stopover = tempfile.mkstemp(prefix="siskin-")
        shellout(""" echo "online_identifier" > {output}""", output=stopover)
        # Include OA list, refs #11579.
        shellout(
            """curl -s https://pub.uni-bielefeld.de/download/2913654/2913655 |
                    cut -d, -f1,2 |
                    tr -d '"' |
                    grep -E '[0-9]{{4,4}}-[0-9]{{3,3}}[0-9xX]' |
                    tr ',' '\n' |
                    sort -u |
                    grep -v ^$ >> {output}""",
            output=stopover,
            preserve_whitespace=True,
        )
        luigi.LocalTarget(stopover).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLFreeContent(AMSLTask):
    """
    Free content. Revelant for OA flags.
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def run(self):
        output = shellout(
            "curl -s '{base}/inhouseservices/list?do=freeContent' | jq -rc . > {output}",
            base=self.config.get("amsl", "base"),
        )
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLOpenAccessKBART(AMSLTask):
    """
    Create a KBART file that contains open access and freely available journals only.

    Used in conjunction with [span-oa-filter](https://git.io/vdB29).
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def run(self):
        """
        Download, maybe unzip, combine with Gold List.
        """
        key = "http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS"
        link = "%s%s" % (self.config.get("amsl", "uri-download-prefix"), key)

        downloaded = shellout("curl --fail {link} > {output} ", link=link)
        _, stopover = tempfile.mkstemp(prefix="siskin-")

        try:
            _ = zipfile.ZipFile(downloaded)
            output = shellout("unzip -p {input} >> {output}", input=downloaded)
        except zipfile.BadZipfile:
            # At least the file is not a zip.
            output = shellout("cat {input} >> {output}", input=downloaded)

        # Include OA list, refs #11579.
        shellout(
            """curl -s https://pub.uni-bielefeld.de/download/2913654/2913655 | cut -d, -f1,2 | tr -d '"' |
                    grep -E '[0-9]{{4,4}}-[0-9]{{3,3}}[0-9xX]' | tr ',' '\n' |
                    awk '{{ print "\t\t"$0 }}' >> {output}""",
            output=output,
            preserve_whitespace=True,
        )

        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class AMSLFilterConfigFreeze(AMSLTask):
    """
    Create a frozen file. File will contain the filterconfig plus content of all URLs.

    Note: "reduced" filterconfig is deprecated.
    """

    date = luigi.DateParameter(default=datetime.date.today())
    style = luigi.Parameter(
        default="default", description="licensing style, e.g. default or reduced"
    )

    def requires(self):
        if self.style == "default":
            return AMSLFilterConfigPatched(date=self.date)
        elif self.style == "reduced":
            return AMSLFilterConfigReduced(date=self.date)
        else:
            raise ValueError("valid filter-config-style values: default, reduced")

    def run(self):
        output = shellout(
            "span-freeze -b -o {output} < {input}", input=self.input().path
        )
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="zip"))


class AMSLFilterConfigReduced(AMSLTask):
    """
    status: deprecated, use "default" filter config again

    Reduced AMSL filter config. Only keep the holdings files associated with an
    institution.

    We only need ISIL and holdings file, e.g.

    $ taskcat AMSLService |
        jq -rc '.[] | select(.evaluateHoldingsFileForLibrary == "yes" and .shardLabel == "UBL-ai") | [.ISIL, .DokumentURI] | @tsv' |
        sort -u

    DE-105  http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-105  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DE105
    DE-105  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-14   http://amsl.technology/discovery/metadata-usage/Dokument/BASE_DE14
    DE-14   http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-14   http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-15   http://amsl.technology/discovery/metadata-usage/Dokument/BASE_DE15
    DE-15   http://amsl.technology/discovery/metadata-usage/Dokument/EBOOKS_KBART_DE15
    DE-15   http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-15   http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DE15/1
    DE-15   http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-1972 http://amsl.technology/discovery/metadata-usage/Dokument/BASE_DE1972
    DE-1972 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-1972 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DE1972
    DE-1972 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-540  http://amsl.technology/discovery/metadata-usage/Dokument/BASE_DE540
    DE-540  http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-540  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DE540
    DE-540  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-82   http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-82   http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DE82
    DE-82   http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Bn3  http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Bn3  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-Bn3  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Brt1 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Brt1 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-Brt1 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Ch1  http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Ch1  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DECh1
    DE-Ch1  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-D161 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-D161 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-D161 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-D275 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-D275 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-D275 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Frei50       http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEFrei50
    DE-Gla1 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Gla1 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-Gla1 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-L152 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-L152 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEL152
    DE-L152 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-L229 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-L229 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-L229 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-L242 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEL242
    DE-Mh31 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Mh31 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEMh31
    DE-Mh31 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Pl11 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Pl11 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-Pl11 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Rs1  http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Rs1  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEGla1
    DE-Rs1  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Trs1 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DETro1
    DE-Zi4  http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Zi4  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_DEZi4
    DE-Zi4  http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    DE-Zwi2 http://amsl.technology/discovery/metadata-usage/Dokument/GOLD_OA_LISTE
    DE-Zwi2 http://amsl.technology/discovery/metadata-usage/Dokument/KBART_FREEJOURNALS
    FID-BBI-DE-23   http://amsl.technology/discovery/metadata-usage/Dokument/BASE_23FIDBBI
    FID-BBI-DE-23   http://amsl.technology/discovery/metadata-usage/Dokument/KBART_23FIDBBI_2022_04_07
    FID-MEDIEN-DE-15        http://amsl.technology/discovery/metadata-usage/Dokument/BASE_DE15FID
    FID-MEDIEN-DE-15        http://amsl.technology/discovery/metadata-usage/Dokument/FID_ISSN_Filter

    We want:

        {
            "DE-Zi4": {"holdings": {"files": ["a.txt", "b.txt", ...]}}
            ...
        }

    TODO: * crossref-only nameless attachments
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return AMSLService(date=self.date)

    def run(self):
        Entry = collections.namedtuple("Entry", "uri source_id")
        with self.input().open() as f:
            docs = json.load(f)
        hfs = collections.defaultdict(set)
        for doc in docs:
            # {
            #   "evaluateHoldingsFileForLibrary": "no",
            #   "ISIL": "DE-1972",
            #   "megaCollection": "Digital Concert Hall",
            #   "productISIL": "ZDB-176-DCH",
            #   "shardLabel": "UBL-main",
            #   "sourceID": "0",
            #   "technicalCollectionID": "sid-0-col-zdb176dch"
            # },
            if doc.get("DokumentLabel") == "GOLD_OA_LISTE":
                # GOLD_OA_LISTE is outdated
                continue
            if doc.get("shardLabel") != "UBL-ai":
                continue
            if doc.get("evaluateHoldingsFileForLibrary") == "no":
                continue
            if not doc.get("ISIL") or not doc.get("DokumentURI"):
                continue
            hfs[doc["ISIL"]].add(
                Entry(uri=doc["DokumentURI"], source_id=doc["sourceID"])
            )

        prefix = self.config.get("amsl", "uri-download-prefix")
        if not prefix:
            raise ValueError("invalid uri download prefix")

        config = {}
        # TODO: write a config higher level helper util for this
        for k, vs in hfs.items():
            doc = {
                "and": [
                    {
                        "source": list(set(v.source_id for v in vs)),
                    },
                    {
                        "holdings": {
                            "files": ["{}{}".format(prefix, v.uri) for v in vs],
                        }
                    },
                ],
            }
            config[k] = doc

        with self.output().open("w") as output:
            json.dump(config, output)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="json"))


class AMSLFilterConfig(AMSLTask):
    """
    Turn AMSL API to a span(1) filter configuration.

    Cases (Spring 2017):

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

    This task turns an AMSL discovery API response into a filterconfig[1], which
    span(1) can understand.

    AMSL API might not specify everything we need to know, so this task shall
    be the only place, where workarounds happen.

    While span-tag is fast, it is not fast enough to iterate over a disjuction
    of 60K items for each of the 100M documents fast enough, which - if we
    could - would simplify the implementation of this task.

    The main speed improvement comes from using lists of collection names
    instead of having each collection processed separately - which is how it
    works conceptually: Each collection could use a separate KBART file (or use
    none at all).

    We ignore collection names, if (external) content files are used. These
    content files are usually there, because we cannot infer the collection
    name from the data alone.

    Performance data point: 22 ISIL each with between 1 and 26 alternatives for
    attachment, each alternative consisting of around three filters. Around 30
    holding or content files each with between 10 and 50000 entries referenced
    about 200 times in total: around 20k records/s.

    Case table (Feb 2019), X/-/o, yes, no, maybe.

    SID COLL ISIL LTHF LTCF ELTCF PI TCID
    -------------------------------------
    X   X    X    -    -    -     -   o
    X   X    X    X    -    -     -   o
    X   X    X    X    X    -     -   o
    X   X    X    X    -    X     -   o
    X   X    X    X    -    -     X   o
    X   X    X    -    X    -     -   o
    X   X    X    -    -    X     -   o
    X   X    X    -    -    -     X   o

    For a transition period, we extend the collection list from AMSL with
    canoncical names via DOI prefix, see #13587. The mapping is fixed and need
    to be updated manually.

    ----

    [1] https://git.io/vQohE

    Fixups, e.g. #23256: edit config file, create diff, apply:

        $ patch $(taskoutput AMSLFilterConfig) < 23256.patch

    """

    date = luigi.DateParameter(default=datetime.date.today())

    def extend_collections(self, colls):
        """
        Given a list of collection names, extend the list by adding the canonicals names as well, refs #13587.
        """
        if not hasattr(self, "_name_to_canonical"):
            with open(self.assets("amsl/13587.json")) as handle:
                self._name_to_canonical = json.load(handle)

        result = set()
        for c in colls:
            result.add(c)
            if c in self._name_to_canonical:
                result.add(self._name_to_canonical[c])

        self.logger.debug(
            "extended collection list from %d to %d items (%d mappings)"
            % (len(colls), len(result), len(self._name_to_canonical))
        )
        return list(result)

    def requires(self):
        return AMSLService(date=self.date)

    def run(self):
        with self.input().open() as handle:
            doc = json.loads(handle.read())

        # Case: ISIL, SID, collection.
        isilsidcollections = collections.defaultdict(
            lambda: collections.defaultdict(set)
        )

        # Case: ISIL, SID, collection, link.
        isilsidlinkcollections = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(set))
        )

        # Ready-made filters per ISIL. Some filters can be added on-the-fly
        # because there aren't many occurences.
        isilfilters = collections.defaultdict(list)

        for item in doc:
            isil, sid, mega_collection, technicalCollectionID = operator.itemgetter(
                "ISIL", "sourceID", "megaCollection", "technicalCollectionID"
            )(item)

            if sid == "48":  # Handled elsewhere.
                continue

            if item.get("DokumentLabel") == "EBOOKS_KBART_DE-15":
                isilfilters[isil].append(
                    {
                        "and": [
                            {
                                "source": [sid],
                            },
                            {
                                "isbn": {
                                    "link": item.get("linkToHoldingsFile"),
                                }
                            },
                        ],
                    }
                )
                continue

            # refs #10495, a subject filter for a few hard-coded ISIL.
            if sid == "34" and isil in ("DE-L152", "DE-1156", "DE-1972", "DE-Kn38"):
                isilfilters[isil].append(
                    {
                        "and": [
                            {
                                "source": ["34"],
                            },
                            {
                                "subject": [
                                    "Music",
                                    "Music education",
                                ]
                            },
                        ]
                    }
                )
                continue

            # refs #10495, maybe use a TSV with custom column name to use a subject list?
            if sid == "34" and isil == "FID-MEDIEN-DE-15":
                isilfilters[isil].append(
                    {
                        "and": [
                            {
                                "source": ["34"],
                            },
                            {
                                "subject": [
                                    "Film studies",
                                    "Information science",
                                    "Mass communication",
                                ]
                            },
                        ]
                    }
                )
                continue

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    -    -    -     -   o
            if dictcheck(
                item,
                contains=["sourceID", "megaCollection", "ISIL"],
                absent=[
                    "linkToHoldingsFile",
                    "linkToContentFile",
                    "externalLinkToContentFile",
                    "productISIL",
                ],
                ignore=["technicalCollectionID"],
            ):
                isilsidcollections[isil][sid].add(mega_collection)
                if technicalCollectionID:
                    isilsidcollections[isil][sid].add(technicalCollectionID)

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    -    -    -     X   o
            elif dictcheck(
                item,
                contains=["sourceID", "megaCollection", "ISIL", "productISIL"],
                absent=[
                    "linkToHoldingsFile",
                    "linkToContentFile",
                    "externalLinkToContentFile",
                ],
                ignore=["technicalCollectionID"],
            ):
                isilsidcollections[isil][sid].add(mega_collection)
                self.logger.debug(
                    "productISIL given, but ignored: %s, %s, %s",
                    isil,
                    sid,
                    item["productISIL"],
                )
                if technicalCollectionID:
                    isilsidcollections[isil][sid].add(technicalCollectionID)

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    X    -    -     X   o
            elif dictcheck(
                item,
                contains=[
                    "sourceID",
                    "megaCollection",
                    "ISIL",
                    "linkToHoldingsFile",
                    "productISIL",
                ],
                absent=["linkToContentFile", "externalLinkToContentFile"],
                ignore=["technicalCollectionID"],
            ):
                self.logger.debug(
                    "productISIL is set, but we do not have a filter for it yet: %s, %s, %s",
                    isil,
                    sid,
                    mega_collection,
                )

                if item.get("evaluateHoldingsFileForLibrary") == "yes":
                    isilsidlinkcollections[isil][sid][item["linkToHoldingsFile"]].add(
                        mega_collection
                    )
                    if technicalCollectionID:
                        isilsidlinkcollections[isil][sid][
                            item["linkToHoldingsFile"]
                        ].add(technicalCollectionID)
                else:
                    self.logger.warning(
                        "evaluateHoldingsFileForLibrary=no plus link: skipping %s", item
                    )

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    X    -    -     -   o
            elif dictcheck(
                item,
                contains=["sourceID", "megaCollection", "ISIL", "linkToHoldingsFile"],
                absent=[
                    "linkToContentFile",
                    "externalLinkToContentFile",
                    "productISIL",
                ],
                ignore=["technicalCollectionID"],
            ):
                if item.get("evaluateHoldingsFileForLibrary") == "yes":
                    isilsidlinkcollections[isil][sid][item["linkToHoldingsFile"]].add(
                        mega_collection
                    )
                    if technicalCollectionID:
                        isilsidlinkcollections[isil][sid][
                            item["linkToHoldingsFile"]
                        ].add(technicalCollectionID)
                else:
                    self.logger.warning(
                        "evaluateHoldingsFileForLibrary=no plus link: skipping %s", item
                    )

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    -    -    X     -   o
            elif dictcheck(
                item,
                contains=[
                    "sourceID",
                    "megaCollection",
                    "ISIL",
                    "externalLinkToContentFile",
                ],
                absent=["linkToHoldingsFile", "linkToContentFile", "productISIL"],
                ignore=["technicalCollectionID"],
            ):
                isilfilters[isil].append(
                    {
                        "and": [
                            {"source": [sid]},
                            {"holdings": {"urls": [item["externalLinkToContentFile"]]}},
                        ]
                    }
                )

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    -    X    -     -   o
            elif dictcheck(
                item,
                contains=["sourceID", "megaCollection", "ISIL", "linkToContentFile"],
                absent=[
                    "linkToHoldingsFile",
                    "externalLinkToContentFile",
                    "productISIL",
                ],
                ignore=["technicalCollectionID"],
            ):
                isilfilters[isil].append(
                    {
                        "and": [
                            {"source": [sid]},
                            {"holdings": {"urls": [item["linkToContentFile"]]}},
                        ]
                    }
                )

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    X    -    X     -   o
            elif dictcheck(
                item,
                contains=[
                    "sourceID",
                    "megaCollection",
                    "ISIL",
                    "linkToHoldingsFile",
                    "externalLinkToContentFile",
                ],
                absent=["linkToContentFile", "productISIL"],
                ignore=["technicalCollectionID"],
            ):
                if item.get("evaluateHoldingsFileForLibrary") == "yes":
                    isilfilters[isil].append(
                        {
                            "and": [
                                {"source": [sid]},
                                {
                                    "holdings": {
                                        "urls": [item["externalLinkToContentFile"]]
                                    }
                                },
                                {"holdings": {"urls": [item["linkToHoldingsFile"]]}},
                            ]
                        }
                    )
                else:
                    self.logger.warning(
                        "evaluateHoldingsFileForLibrary=no plus link: skipping %s", item
                    )

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # X   X    X    X    X    -     -   o
            elif dictcheck(
                item,
                contains=[
                    "sourceID",
                    "megaCollection",
                    "ISIL",
                    "linkToHoldingsFile",
                    "linkToContentFile",
                ],
                absent=["externalLinkToContentFile", "productISIL"],
                ignore=["technicalCollectionID"],
            ):
                if item.get("evaluateHoldingsFileForLibrary") == "yes":
                    isilfilters[isil].append(
                        {
                            "and": [
                                {"source": [sid]},
                                {"holdings": {"urls": [item["linkToContentFile"]]}},
                                {"holdings": {"urls": [item["linkToHoldingsFile"]]}},
                            ]
                        }
                    )
                else:
                    self.logger.warning(
                        "evaluateHoldingsFileForLibrary=no plus link: skipping %s", item
                    )

            # SID COLL ISIL LTHF LTCF ELTCF PI TCID
            # -------------------------------------
            # ?   ?    ?    ?    ?    ?     ?   o
            else:
                raise RuntimeError(
                    "unhandled combination of sid, collection and other parameters: %s",
                    item,
                )

        # A second pass.
        for isil, blob in list(isilsidcollections.items()):
            for sid, colls in list(blob.items()):
                if sid == "49":
                    # TODO: too broad?
                    # isilfilters[isil].append({"source": [sid]})
                    pass
                else:
                    isilfilters[isil].append(
                        {
                            "and": [
                                {"source": [sid]},
                                {"collection": sorted(self.extend_collections(colls))},
                            ]
                        }
                    )

        # A second pass.
        for isil, blob in list(isilsidlinkcollections.items()):
            for sid, spec in list(blob.items()):
                for link, colls in list(spec.items()):
                    if sid == "49":
                        isilfilters[isil].append(
                            {
                                "and": [
                                    {
                                        "source": [sid],
                                    },
                                    {
                                        "holdings": {
                                            "urls": [link],
                                        },
                                    },
                                ]
                            }
                        )
                    else:
                        isilfilters[isil].append(
                            {
                                "and": [
                                    {
                                        "source": [sid],
                                    },
                                    {
                                        "collection": sorted(
                                            self.extend_collections(colls)
                                        )
                                    },
                                    {
                                        "holdings": {
                                            "urls": [link],
                                        },
                                    },
                                ]
                            }
                        )

        # Final assembly.
        filterconfig = collections.defaultdict(dict)
        for isil, filters in list(isilfilters.items()):
            if len(filters) == 0:
                continue
            if len(filters) == 1:
                filterconfig[isil] = filters[0]
                continue
            filterconfig[isil] = {"or": filters}

        # XXX: Adjust a few items for DE-14, cf. 2018-06-11, namely, add links
        # to external holding files, which are not included into the AMSL
        # discovery API response, refs #13378.
        fix_url = "https://dbod.de/SLUB-EZB-KBART.zip"
        for term in filterconfig["DE-14"]["or"]:
            for t in term["and"]:
                if ("holdings" not in t) and ("urls" not in t.get("holdings", [])):
                    continue
                if fix_url in t["holdings"]["urls"]:
                    continue
                t["holdings"]["urls"].append("https://dbod.de/SLUB-EZB-KBART.zip")

        with self.output().open("w") as output:
            json.dump(filterconfig, output, cls=SetEncoder)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="json"))


class AMSLFilterConfigPatched(AMSLTask):
    """
    Apply patches to AMSLFilterConfig configuration file.
    """

    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return AMSLFilterConfig(date=self.date)

    def run(self):
        # $ dpkg -S replace | grep mariadb
        # mariadb-server-10.6: /usr/share/man/man1/replace.1.gz
        # mariadb-server-10.6: /usr/bin/replace

        # temporary patch until links for BBI are fixed in AMSL
        a = """{"and":[{"source":["49"]},{"holdings":{"urls":["https://live.amsl.technology/OntoWiki/files/get?setResource=http://amsl.technology/discovery/metadata-usage/Dokument/BASE_23FIDBBI"]}}]}"""
        b = """{"and":[{"source":["49"]},{"issn":{"url":"https://live.amsl.technology/OntoWiki/files/get?setResource=http://amsl.technology/discovery/metadata-usage/Dokument/KBART_23FIDBBI_2022_04_07"}}]}"""
        output = shellout(
            """ jq -c . {input} | replace '{a}' '{b}' > {output} """,
            a=a,
            b=b,
            input=self.input().path,
        )  # need to compact first
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="json"))


class AMSLCollectionList(AMSLTask):
    """
    TODO: implement.

    Find all collection names used in AMSL and their canonical name, via
    members API, prefix and names.
    """

    def run(self):
        raise NotImplementedError()
