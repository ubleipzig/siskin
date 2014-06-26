# coding: utf-8
# pylint: disable=F0401,C0111,W0232,E1101,E1103,C0301

"""
VIAF-related tasks.
"""

from gluish.benchmark import timed
from gluish.esindex import CopyToIndex
from gluish.format import TSV
from gluish.parameter import ClosestDateParameter
from gluish.utils import shellout
from siskin.task import BaseTask
import BeautifulSoup
import datetime
import luigi
import re
import requests

class VIAFTask(BaseTask):
    TAG = 'viaf'

    def closest(self):
        task = VIAFLatestDate()
        luigi.build([task], local_scheduler=True)
        with task.output().open() as handle:
            date, _ = handle.iter_tsv(cols=('date', 'url')).next()
            dateobj = datetime.date(*map(int, date.split('-')))
        return dateobj

class VIAFDataURLList(VIAFTask):
    """ Download Viaf data page.
        Match on http://viaf.org/viaf/data/viaf-20140215-links.txt.gz
    """
    date = luigi.DateParameter(default=datetime.date.today())
    url = luigi.Parameter(default='http://viaf.org/viaf/data/')

    def run(self):
        r = requests.get(self.url)
        if not r.status_code == 200:
            raise RuntimeError(r)

        strainer = BeautifulSoup.SoupStrainer('a')
        soup = BeautifulSoup.BeautifulSoup(r.text, parseOnlyThese=strainer)
        with self.output().open('w') as output:
            for link in soup:
                output.write_tsv(link.get('href'))

    def output(self):
        return luigi.LocalTarget(path=self.path(digest=True), format=TSV)

class VIAFLatestDate(VIAFTask):
    """" The latest date for clusters file """
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return VIAFDataURLList()

    def run(self):
        with self.input().open() as handle:
            for row in handle:
                pattern = r"http://viaf.org/viaf/data/viaf-(\d{8})-clusters-rdf.nt.gz"
                mo = re.match(pattern, row)
                if mo:
                    date = datetime.datetime.strptime(mo.group(1), '%Y%m%d').date()
                    with self.output().open('w') as output:
                        output.write_tsv(date, mo.group())
                    break
            else:
                raise RuntimeError('Could not find latest date.')

    def output(self):
        return luigi.LocalTarget(path=self.path(), format=TSV)

class VIAFDump(VIAFTask):
    """ Download the latest dump. Dynamic, uses the link from VIAFLatestDate. """

    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return VIAFLatestDate()

    def run(self):
        with self.input().open() as handle:
            _, url = handle.iter_tsv(cols=('date', 'url')).next()
            output = shellout("wget -c --retry-connrefused '{url}' -O {output}",
                              url=url)
            luigi.File(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='nt.gz'))

class VIAFExtract(VIAFTask):
    """ Extract the dump. """

    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return VIAFDump(date=self.date)

    def run(self):
        output = shellout("gunzip -c {input} > {output}",
                          input=self.input().path)
        luigi.File(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='nt'))

class VIAFSameAs(VIAFTask):
    """ Extract the VIAF sameAs relations. """

    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return VIAFExtract(date=self.date)

    def run(self):
        output = shellout("""grep -F "<http://www.w3.org/2002/07/owl#sameAs>"
                             {input} > {output}""", input=self.input().path,
                             ignoremap={1: "Not found."})
        luigi.File(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='n3'))

class VIAFJson(VIAFTask):
    """ Shorter notation. """

    date = ClosestDateParameter(default=datetime.date.today())

    def requires(self):
        return VIAFExtract(date=self.date)

    @timed
    def run(self):
        output = shellout("""nttoldj -a -i {input} |
            grep -Fv "This primary entity identifier is deprecated" |
            grep -Fv "This concept identifier is deprecated" |
            grep -Fv "foaf:primaryTopic" |
            grep -Fv "void:inDataset" |
            grep -Fv "foaf:focus" |
            grep -Fv "foaf:Document" |
            grep -Fv "/#foaf:Organization" |
            grep -Fv "/#rdaEnt:CorporateBody" |
            grep -Fv "/#foaf:Person" > {output}""",
            input=self.input().path)
        luigi.File(output).move(self.output().path)

    def output(self):
        return luigi.LocalTarget(path=self.path(ext='ldj'))

class VIAFIndex(VIAFTask, CopyToIndex):
    date = ClosestDateParameter(default=datetime.date.today())

    index = 'viaf'
    doc_type = 'triples'
    purge_existing_index = True

    def update_id(self):
        """ This id will be a unique identifier for this indexing task."""
        return self.effective_task_id()

    def requires(self):
        return VIAFJson(date=self.date)
