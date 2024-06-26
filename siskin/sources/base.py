# coding: utf-8
# pylint: disable=C0301,E1101

# Copyright 2016 by Leipzig University Library, http://ub.uni-leipzig.de
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
BASE, refs #5994.

* https://www.base-search.net/
* https://api.base-search.net/
* https://en.wikipedia.org/wiki/BASE_(search_engine)
* http://www.dlib.org/dlib/june04/lossau/06lossau.html

Currently (Dec 2018) BASE is provided via SLUB download.

Config
------

[base]

ftp-host = sftp://example.com
ftp-base = /target_data/xyz
ftp-username= admin
ftp-password= s3cr3t
ftp-pattern = *
"""

import collections
import datetime
import functools
import json
import os
import re
import tempfile

import luigi
import requests
from gluish.format import TSV, Gzip, Zstd
from gluish.intervals import monthly
from gluish.parameter import ClosestDateParameter
from gluish.utils import shellout

from siskin.common import FTPMirror
from siskin.task import DefaultTask


class BaseTask(DefaultTask):
    """
    Various tasks around base, refs #14947.

    As of 08/2022, we only implement access to the latest version, i.e. no date
    parameter.
    """

    TAG = "126"

    # default BASE download URL
    download_url = "https://download.ubl-proxy.slub-dresden.de/base"

    def closest(self):
        return monthly(date=self.date)

    @functools.lru_cache
    def get_last_modified_date(self):
        last_modified_header = requests.head(self.download_url).headers["Last-Modified"]
        last_modified = datetime.datetime.strptime(
            last_modified_header, "%a, %d %b %Y %H:%M:%S %Z"
        )
        return last_modified


class BasePaths(BaseTask):
    """
    Mirror SLUB FTP for base. Deprecated.
    """

    date = luigi.DateParameter(default=datetime.date.today())
    max_retries = luigi.IntParameter(default=10, significant=False)
    timeout = luigi.IntParameter(
        default=20, significant=False, description="timeout in seconds"
    )

    def requires(self):
        return FTPMirror(
            host=self.config.get("base", "ftp-host"),
            base=self.config.get("base", "ftp-base"),
            username=self.config.get("base", "ftp-username"),
            password=self.config.get("base", "ftp-password"),
            pattern=self.config.get("base", "ftp-pattern"),
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

    def run(self):
        self.input().move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class BaseDirectDownload(BaseTask):
    """
    Direct download link.
    """

    url = luigi.Parameter(
        default="https://download.ubl-proxy.slub-dresden.de/base", significant=False
    )

    def run(self):
        output = shellout(
            """ curl --output {output} --fail -sL "{url}" """,
            url=self.url,
        )
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        last_modified = self.get_last_modified_date()
        filename = "base-{}.tar.gz".format(last_modified.strftime("%Y-%m-%d"))
        return luigi.LocalTarget(path=self.path(filename=filename), format=Gzip)


class BaseFix(BaseTask):
    """
    On-the-fly fixes.
    """

    style = luigi.Parameter(
        default="z", description="gzip in tar (z) or tar.gz (tgz)", significant=False
    )

    def requires(self):
        return BaseDirectDownload()

    def run(self):
        # SOLR has a limit on facet_fields value length.
        max_length = 4000
        pat_year = re.compile(r"[1-9][0-9][0-9][0-9]")
        with tempfile.NamedTemporaryFile() as f:
            if self.style == "z":
                shellout(
                    "tar -xOf {input} | zcat | span-doisniffer -S > {output}",
                    input=self.input().path,
                    output=f.name,
                )
            elif self.style == "tgz":
                shellout(
                    "tar -xOzf {input} | span-doisniffer -S > {output}",
                    input=self.input().path,
                    output=f.name,
                )
            f.flush()
            f.seek(0)
            stats = collections.Counter()
            self.logger.debug("applying fixes...")
            with self.output().open("w") as output:
                for line in f:
                    stats["total"] += 1
                    line = line.replace(b"DE-15-FID", b"FID-MEDIEN-DE-15")
                    doc = json.loads(line)
                    # we can decode w/o the base64 padding
                    doc["recordtype"] = "default"  # refs #23424
                    doc["id"] = doc["id"].replace("=", "")
                    # possible analysis error: Document contains at least one
                    # immense term in field=\"title_fullStr\" (whose UTF8
                    # encoding is longer than the max length 32766), all of
                    # which were skipped.  Please correct the analyzer to not
                    # produce such terms.
                    for key in ("title", "title_full", "title_short", "title_sort"):
                        if key in doc:
                            doc[key] = doc[key][:max_length]
                    if "author" in doc:
                        if isinstance(doc["author"], str):
                            doc["author"] = doc["author"][:max_length]
                            stats["author.isstr"] += 1
                        else:
                            for i, v in enumerate(doc["author"]):
                                if not v:
                                    stats["author.isempty"] += 1
                                    continue
                                doc["author"][i] = v[:max_length]
                            stats["author.islist"] += 1
                    if "author_sort" in doc:
                        doc["author_sort"] = doc["author_sort"][:max_length]
                    if "author_facet" in doc:
                        for i, v in enumerate(doc["author_facet"]):
                            if not v:
                                continue
                            doc["author_facet"][i] = v[:max_length]
                    if "publishDate" in doc:
                        m = pat_year.search(doc["publishDate"])
                        if m:
                            doc["publishDate"] = m.group()
                    output.write(json.dumps(doc).encode("utf-8"))
                    output.write(b"\n")

        self.logger.debug("{}".format(stats))

        # if self.style == "z":
        #     output = shellout(
        #         """
        #     tar -xOf {input} | zcat |
        #     jq -rc '.author[0] = .author[0][0:4000] |
        #             .author_sort = .author_sort[0:4000] |
        #             .author_facet[0] = .author_facet[0][0:4000] |
        #             .publishDate = (.publishDate // "" | scan("[1-9][0-9][0-9][0-9]")) // ""' |
        #     sed -e 's@"DE-15-FID"@"FID-MEDIEN-DE-15"@' |
        #     span-doisniffer -S |
        #     zstd -T0 -c > {output}
        #     """,
        #         input=self.input().path,
        #     )
        #     luigi.LocalTarget(output).move(self.output().path)
        # elif self.style == "tgz":
        #     output = shellout(
        #         """
        #     tar -xOzf {input} |
        #     jq -rc '.author[0] = .author[0][0:4000] |
        #             .author_sort = .author_sort[0:4000] |
        #             .author_facet[0] = .author_facet[0][0:4000] |
        #             .publishDate = (.publishDate // "" | scan("[1-9][0-9][0-9][0-9]")) // ""' |
        #     sed -e 's@"DE-15-FID"@"FID-MEDIEN-DE-15"@' |
        #     span-doisniffer -S |
        #     zstd -T0 -c > {output}
        #     """,
        #         input=self.input().path,
        #     )
        #     luigi.LocalTarget(output).move(self.output().path)
        # else:
        #     raise ValueError("supported --style: z, tgz")

    def output(self):
        last_modified = self.get_last_modified_date()
        filename = "base-{}.zst".format(last_modified.strftime("%Y-%m-%d"))
        return luigi.LocalTarget(path=self.path(filename=filename), format=Zstd)


class BaseSingleFile(BaseTask):
    """
    Create a single compressed file of tarball. Deprecated, use BaseFix.
    """

    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return BasePaths(date=self.date)

    def run(self):
        with self.input().open() as handle:
            paths = [p.strip().decode("utf-8") for p in handle.readlines()]

        # SOLR has a limit on facet_fields value length.
        sanitize = """
        jq -rc '.author[0] = .author[0][0:4000] |
                .author_sort = .author_sort[0:4000] |
                .author_facet[0] = .author_facet[0][0:4000] |
                .publishDate = (.publishDate // "" | scan("[1-9][0-9][0-9][0-9]")) // ""'
        """

        for path in paths:
            if not path.endswith("finc/latest"):
                continue

            realpath = os.path.realpath(path)
            # Since 12/2019 symlinks might be an absolute path (on the server),
            # which makes this more flaky. Assume, that symlink points to the
            # same directory.
            if realpath.startswith("/"):
                self.logger.debug(
                    "absolute path detected; assuming symlinked file is in the same directory"
                )
                realpath = os.path.join(
                    os.path.dirname(path), os.path.basename(realpath)
                )
            self.logger.debug("found: %s", realpath)
            if not realpath.endswith("gz"):
                raise RuntimeError("want gz (tarball), got: %s", realpath)
            decomp = "unpigz -c"
            if realpath.endswith("tar.gz"):
                decomp = "tar -xOzf"
            self.logger.debug("fixing isil on the fly, refs #20232")
            output = shellout(
                """ {decomp} "{input}" |
                                  {sanitize} |
                                  sed -e 's@"DE-15-FID"@"FID-MEDIEN-DE-15"@' |
                                  doisniffer -S |
                                  pigz -c > {output}""",
                decomp=decomp,
                input=realpath,
                sanitize=sanitize,
            )
            luigi.LocalTarget(output).move(self.output().path)
            break
        else:
            raise RuntimeError("no finc/latest in %s", paths)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext="ndj.gz"), format=Gzip)
