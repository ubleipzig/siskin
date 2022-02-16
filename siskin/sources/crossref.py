# coding: utf-8
# pylint: disable=C0301,C0330,W0622,E1101

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
https://www.crossref.org/

CrossRef is an association of scholarly publishers
that develops shared infrastructure to support
more effective scholarly communications.

Our citation-linking network today covers over 68
million journal articles and other content items
(books chapters, data, theses, technical reports)
from thousands of scholarly and professional
publishers around the globe.

Configuration
-------------

[crossref]

doi-blacklist = /tmp/siskin-data/crossref/CrossrefDOIBlacklist/output.tsv

"""

# TODO: see, if
# https://academictorrents.com/details/e4287cb7619999709f6e9db5c359dda17e93d515
# is usable, and how often it gets updated
# https://www.crossref.org/blog/new-public-data-file-120-million-metadata-records/

import datetime
import io
import itertools
import json
import os
import socket
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import requests
from six import string_types

import elasticsearch
import luigi
from gluish.common import Executable
from gluish.format import TSV, Gzip
from gluish.intervals import monthly
from gluish.parameter import ClosestDateParameter
from gluish.utils import date_range, shellout
from siskin import __version__
from siskin.benchmark import timed
from siskin.mail import send_mail
from siskin.sources.amsl import AMSLFilterConfig, AMSLService
from siskin.task import DefaultTask
from siskin.utils import URLCache, load_set_from_target


class CrossrefTask(DefaultTask):
    """
    Crossref related tasks. See: http://www.crossref.org/
    """
    TAG = '49'

    def closest(self):
        """
        Update frequency.
        """
        return monthly(date=self.date)


class CrossrefRawItems(CrossrefTask):
    """
    Concatenate all harvested items.

    TODO: we can get rid of all tasks before this with span-crossref-sync;

    $ span-crossref-sync -t 30m -mode s -verbose -s 2021-04-27 > /dev/null
    $ time cat $(find ~/.cache/span/crossref-sync/ -type f -name "*gz") >> $(taskoutput CrossrefRawItems)

    or:

    $ span-crossref-sync -t 30m -mode s -verbose -s 2021-04-27 | pigz -c > $(taskoutput CrossrefRawItems)

    Companion cron:

    28 1 * * *  span-crossref-sync -t 30m -mode s -verbose -s 2021-04-27 > /dev/null

    Most updates so far in a single day on 2021-12-22: 10,120,570.

    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())
    update = luigi.Parameter(default='days', description='days, weeks or months')

    def run(self):
        crossref_sync_dir = self.config.get("crossref", "sync-dir")
        output = shellout("""
                 span-crossref-sync -t 30m -s {begin} -c {crossref_sync_dir} >> {output}
                 """,
                          begin=self.begin,
                          crossref_sync_dir=crossref_sync_dir)  # 22min
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='ldj.gz'), format=Gzip)


class CrossrefUniqItems(CrossrefTask):
    """
    Calculate current snapshot via span-crossref-snapshot. About 204m30.910s;
    takes 99m59.783s to extract a value with jq (and parallel).

    With span-crossref-{sync,snapshot} we get 130377934 unique records.

    Cf. https://www.crossref.org/06members/53status.html
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return CrossrefRawItems(begin=self.begin, date=self.closest())

    def run(self):
        output = shellout("span-crossref-snapshot -verbose -z -o {output} {input}", input=self.input().path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='ldj.gz'), format=Gzip)


class CrossrefIntermediateSchema(CrossrefTask):
    """
    Convert to intermediate format via span.
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return {'span': Executable(name='span-import', message='http://git.io/vI8NV'), 'file': CrossrefUniqItems(begin=self.begin, date=self.date)}

    @timed
    def run(self):
        output = shellout("span-import -i crossref <(unpigz -c {input}) | pigz -c > {output}", input=self.input().get('file').path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='ldj.gz'), format=Gzip)


class CrossrefCollections(CrossrefTask):
    """
    A collection of crossref collections, refs. #6985. XXX: Save counts as well.
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return {'input': CrossrefIntermediateSchema(begin=self.begin, date=self.date), 'jq': Executable(name='jq', message='https://github.com/stedolan/jq')}

    @timed
    def run(self):
        output = shellout("""jq -rc '.["finc.mega_collection"][]?' <(unpigz -c {input}) | LC_ALL=C sort -S35% -u > {output}""",
                          input=self.input().get('input').path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefCollectionsCount(CrossrefTask):
    """
    Report collections and the number of titles per collection.
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return {'input': CrossrefIntermediateSchema(begin=self.begin, date=self.date), 'jq': Executable(name='jq', message='https://github.com/stedolan/jq')}

    @timed
    def run(self):
        output = shellout("""jq -rc '.["finc.mega_collection"][]?' <(unpigz -c {input}) | LC_ALL=C sort -S35% > {output}""",
                          input=self.input().get('input').path)

        groups = {}  # Map collection name to its size.
        with open(output) as handle:
            for k, g in itertools.groupby(handle):
                name = k.strip()
                groups[name] = len(list(g))

        with self.output().open('w') as output:
            json.dump(groups, output)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='json'))


class CrossrefCollectionsDifference(CrossrefTask):
    """
    Refs. #7049. Check list of collections against AMSL Crossref collections and
    report difference.

    This task uses an experimental email template in ../assets/mail/7049.tmpl, by
    default no email is sent, only when --to is set to one or more comma
    separated email addresses.
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    to = luigi.Parameter(default=None, description="email address of recipient, comma separated, if multiple")

    def requires(self):
        return {'crossref': CrossrefCollections(begin=self.begin, date=self.date), 'amsl': AMSLService(date=self.date, name='outboundservices:discovery')}

    @timed
    def run(self):
        if self.to is None:
            self.logger.debug("not sending any email, use --to my@mail.com to send out a report")

        amsl = set()

        with self.input().get('amsl').open() as handle:
            items = json.load(handle)

        for item in items:
            if item['sourceID'] == '49':
                amsl.add(item['megaCollection'].strip())

        self.logger.debug("found %s crossref collections in AMSL" % len(amsl))

        missing_in_amsl = []

        with self.input().get('crossref').open() as handle:
            with self.output().open('w') as output:
                for row in handle.iter_tsv(cols=('name', )):
                    if row.name not in amsl:
                        missing_in_amsl.append(row.name)
                        output.write_tsv(row.name)

        self.logger.debug("%s collections seem to be missing in AMSL", len(missing_in_amsl))

        if self.to is not None:
            # Try to send a message, experimental.
            tolist = [v.strip() for v in self.to.split(",")]

            subject = "%s %s %s" % (self.__class__.__name__, datetime.datetime.today().strftime("%Y-%m-%d %H:%M"), len(missing_in_amsl))

            with io.open(self.assets("mail/7049.tmpl"), encoding="utf-8") as fh:
                template = fh.read()

            message = template.format(
                version=__version__,
                count=len(missing_in_amsl),
                clist="\n".join(missing_in_amsl),
                hostname=socket.gethostname(),
                xref=self.input().get("crossref").path,
                amsl=self.input().get("amsl").path,
            )
            message = message.encode("utf-8")
            send_mail(tolist=tolist, subject=subject, message=message)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefDOIList(CrossrefTask):
    """
    A list of Crossref DOIs.
    """
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return {'input': CrossrefIntermediateSchema(date=self.date), 'jq': Executable(name='jq', message='https://github.com/stedolan/jq')}

    @timed
    def run(self):
        _, stopover = tempfile.mkstemp(prefix='siskin-')
        # process substitution sometimes results in a broken pipe, so extract beforehand
        output = shellout("unpigz -c {input} > {output}", input=self.input().get('input').path)
        shellout("""jq -r '.doi?' {input} | grep -o "10.*" 2> /dev/null | LC_ALL=C sort -S50% > {output} """, input=output, output=stopover)
        os.remove(output)
        output = shellout("""sort -S50% -u {input} > {output} """, input=stopover)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefISSNList(CrossrefTask):
    """
    Just dump a list of all ISSN values. With dups and all.
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return {'input': CrossrefUniqItems(begin=self.begin, date=self.date), 'jq': Executable(name='jq', message='https://github.com/stedolan/jq')}

    @timed
    def run(self):
        output = shellout("jq -r '.ISSN[]?' <(unpigz -c {input}) 2> /dev/null > {output}", input=self.input().get('input').path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefUniqISSNList(CrossrefTask):
    """
    Just dump a list of all ISSN values. Sorted and uniq.
    """
    begin = luigi.DateParameter(default=datetime.date(2021, 4, 27), description='2021-04-27 seemed to be the start of the current crossref update streak')
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return CrossrefISSNList(begin=self.begin, date=self.date)

    @timed
    def run(self):
        output = shellout("sort -u {input} > {output}", input=self.input().path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefDOIAndISSNList(CrossrefTask):
    """
    A list of Crossref DOIs with their ISSNs.
    """
    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return {'input': CrossrefIntermediateSchema(date=self.date), 'jq': Executable(name='jq', message='https://github.com/stedolan/jq')}

    @timed
    def run(self):
        _, stopover = tempfile.mkstemp(prefix='siskin-')
        temp = shellout("unpigz -c {input} > {output}", input=self.input().get('input').path)
        output = shellout("""jq -r '[.doi?, .["rft.issn"][]?, .["rft.eissn"][]?] | @csv' {input} | LC_ALL=C sort -S50% > {output} """,
                          input=temp,
                          output=stopover)
        os.remove(temp)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='csv'))


class CrossrefDOIHarvest(CrossrefTask):
    """
    Harvest DOI redirects from doi.org API. This is a long running task. It's
    probably best to run this tasks complete separate from the rest and let
    other processing pipelines use the result, as it is available.

    ----

    It is highly recommended that you put a static entry into /etc/hosts
    for doi.org while `hurrly` is running.

    As of 2015-07-31 doi.org resolves to six servers. Just choose one.

    $ nslookup doi.org

    """
    def requires(self):
        """
        If we have more DOI sources, we could add them as requirements here.
        """
        return {
            'input': CrossrefDOIList(date=datetime.date.today()),
            'hurrly': Executable(name='hurrly', message='http://github.com/miku/hurrly'),
            'pigz': Executable(name='pigz', message='http://zlib.net/pigz/')
        }

    def run(self):
        output = shellout("hurrly -w 4 < {input} | pigz > {output}", input=self.input().get('input').path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='tsv.gz'))


class CrossrefDOIBlacklist(CrossrefTask):
    """
    Create a blacklist of DOIs. Possible cases:

    1. A DOI redirects to http://www.crossref.org/deleted_DOI.html or
       most of these sites below crossref.org: https://gist.github.com/miku/6d754104c51fb553256d
    2. A DOI API lookup does not return a HTTP 200.

    The output of this task should be used as doi-blacklist in config.
    """
    def requires(self):
        return CrossrefDOIHarvest()

    def run(self):
        _, stopover = tempfile.mkstemp(prefix='siskin-')
        shellout("""LC_ALL=C zgrep -E "http(s)?://.*.crossref.org" {input} >> {output}""", input=self.input().path, output=stopover)
        shellout("""LC_ALL=C zgrep -v "^200" {input} >> {output}""", input=self.input().path, output=stopover)
        output = shellout("sort -S50% -u {input} | cut -f4 | sed s@http://doi.org/api/handles/@@g > {output}", input=stopover)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class CrossrefMembers(CrossrefTask):
    """
    Fetch members information via API.
    """
    date = luigi.DateParameter(default=datetime.date.today())

    def run(self):
        output = shellout("span-crossref-members > {output}")
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class CrossrefPrefixList(CrossrefTask):
    """
    DOI prefix and canonical name, refs #13587.
    """
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return CrossrefMembers(date=self.date)

    def run(self):
        """ XXX: multiple prefixes per name """
        output = shellout("""jq -rc '.message.items[] |
                          {{"prefix": .prefixes[], "name": .["primary-name"]}} |
                          [.prefix, .name] | @tsv' < {input} > {output}""",
                          input=self.input().path)
        luigi.LocalTarget(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path())


class CrossrefPrefixMapping(CrossrefTask):
    """
    Map existing collection name to new name.

    Current format: PREFIX CANONICAL-NAME CURRENT-AMSL-MEGACOLLECTION
    """
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return {
            'data': CrossrefIntermediateSchema(date=self.date),
            'list': CrossrefPrefixList(date=self.date),
        }

    def run(self):
        namemap = {}

        with self.input().get('list').open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                if '\t' not in line:
                    self.logger.warn("invalid prefix list row: %s", line)
                    continue
                prefix, name = line.split('\t', 1)
                namemap[prefix.strip()] = name.strip()

        self.logger.debug("found %d mappings from prefix to name", len(namemap))

        result = set()

        with self.input().get('data').open() as handle:
            for i, line in enumerate(handle):
                if i % 1000000 == 0:
                    self.logger.debug("[...] at %d", i)
                doc = json.loads(line.decode('utf-8').strip())
                doi = doc.get("doi")
                if not doi:
                    self.logger.warn("document without doi: %s", line)
                    continue
                prefix, _ = doi.split("/", 1)

                # Most records will have a single collection name.
                for mega_collection in doc.get("finc.mega_collection", []):
                    name = namemap.get(prefix)

                    if name is None:
                        # Cache canonical names, if we missed it.
                        resp = requests.get("https://api.crossref.org/members/%s" % prefix).json()
                        namemap[prefix] = resp["message"]["primary-name"]
                        name = namemap.get(prefix, "UNDEFINED")
                        self.logger.debug("namemap now contains %d entries, added %s, %s", len(namemap), prefix, namemap[prefix])

                    try:
                        name = name.decode('utf-8')
                    except AttributeError as err:
                        pass  # XXX: python 2/3 compat
                    entry = tuple(v for v in (prefix, name, mega_collection))
                    result.add(entry)  # Unique.

        with self.output().open('w') as output:
            self.logger.debug("output at %s", output.name)
            for row in sorted(result):
                output.write_tsv(*row)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefPrefixMappingDiff(CrossrefTask):
    """
    Only emit rows, where canonical and current name differ.
    """
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return CrossrefPrefixMapping(date=self.date)

    def run(self):
        with self.input().open() as handle:
            with self.output().open('w') as output:
                for line in handle:
                    if not isinstance(line, string_types):
                        line = line.decode('utf-8')
                    doi, name, current = line.strip().split('\t')
                    if u'{} (CrossRef)'.format(name) == current:
                        continue
                    if isinstance(line, string_types):
                        line = line.encode('utf-8')
                    output.write(line)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefDataPrefixList(CrossrefTask):
    """
    List of prefixes actually occuring in the data.
    """
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return CrossrefIntermediateSchema(date=self.date)

    def run(self):
        seen = set()

        with self.input().open() as handle:
            for i, line in enumerate(handle):
                if i % 1000000 == 0:
                    self.logger.debug("[...] at %d", i)
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                doi = doc.get("doi")
                if not doi:
                    self.logger.warn("document without doi: %s", line)
                    continue
                prefix, _ = doi.split("/", 1)
                seen.add(prefix)

        with self.output().open('w') as output:
            for value in sorted(seen):
                output.write_tsv(value)

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)


class CrossrefPrefix13587(CrossrefTask):
    """
    Refs #13587, note #32.
    """
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return {
            'seen': CrossrefDataPrefixList(date=self.date),
            'mapping': CrossrefPrefixMapping(date=self.date),
        }

    def run(self):
        seen = load_set_from_target(self.input().get('seen'))
        written = set()
        with self.input().get('mapping').open() as handle:
            with self.output().open('w') as output:
                for row in handle.iter_tsv(cols=('prefix', 'name', 'current')):
                    if row.prefix not in seen:
                        self.logger.debug("not seen: %s", row.prefix)
                        continue
                    cut = row[:2]
                    if tuple(cut) not in written:
                        output.write_tsv(*cut)
                        written.add(tuple(cut))

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)
