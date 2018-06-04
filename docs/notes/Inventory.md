# Inventory (WIP)

* Sources, Source Format, Target Format, Tools (filename, mappings), Workflow, Data Hosts

## Sources

```
$ tasktags | csvtomd
```
Tag       |  Class
----------|-------------------------------------------
adhoc     |  AdhocFormetaSamples
adhoc     |  AdhocTask
adhoc     |  Issue7049
adhoc     |  Issue7049ExportExcel
adhoc     |  K10Matches
adhoc     |  OADOIDatasetStatusByDOI
ai        |  AIAddReferences
ai        |  AIApplyOpenAccessFlag
ai        |  AIBlobDB
ai        |  AICheckStats
ai        |  AICollectionsAndSerialNumbers
ai        |  AICoverageISSN
ai        |  AIDOIList
ai        |  AIDOIRedirectTable
ai        |  AIDOIStats
ai        |  AIErrorDistribution
ai        |  AIExport
ai        |  AIInstitutionChanges
ai        |  AIIntermediateSchema
ai        |  AIIntermediateSchemaDeduplicated
ai        |  AIISSNCoverageCatalogMatches
ai        |  AIISSNCoverageSolrMatches
ai        |  AIISSNList
ai        |  AIISSNOverlaps
ai        |  AIISSNStats
ai        |  AILicensing
ai        |  AILocalData
ai        |  AIQuality
ai        |  AIRedact
ai        |  AITask
ai        |  AIUpdate
amsl      |  AMSLCollections
amsl      |  AMSLCollectionsISIL
amsl      |  AMSLCollectionsISILList
amsl      |  AMSLCollectionsShardFilter
amsl      |  AMSLFilterConfig
amsl      |  AMSLFilterConfigFreeze
amsl      |  AMSLFreeContent
amsl      |  AMSLGoldListKBART
amsl      |  AMSLHoldingsFile
amsl      |  AMSLOpenAccessISSNList
amsl      |  AMSLOpenAccessKBART
amsl      |  AMSLService
amsl      |  AMSLTask
amsl      |  AMSLWisoPackages
b3kat     |  B3KatDownload
b3kat     |  B3KatLinks
b3kat     |  B3KatMARCXML
b3kat     |  B3KatTask
base      |  BaseDownload
base      |  BaseTask
btag      |  BTAGCrossref
btag      |  BTAGCrossrefSet
btag      |  BTAGDOAJSubset
btag      |  BTAGMAGSubset
btag      |  BTAGTask
common    |  CommonTask
common    |  FTPMirror
common    |  HTTPDownload
common    |  RedmineDownload
common    |  RedmineDownloadAttachments
core      |  CoreDownload
core      |  CoreDownloadFulltext
core      |  CoreTask
crossref  |  CrossrefChunkItems
crossref  |  CrossrefCollections
crossref  |  CrossrefCollectionsCount
crossref  |  CrossrefCollectionsDifference
crossref  |  CrossrefCollectionStats
crossref  |  CrossrefDOIAndISSNList
crossref  |  CrossrefDOIBlacklist
crossref  |  CrossrefDOIHarvest
crossref  |  CrossrefDOIList
crossref  |  CrossrefExport
crossref  |  CrossrefGenericItems
crossref  |  CrossrefHarvest
crossref  |  CrossrefHarvestChunkWithCursor
crossref  |  CrossrefHarvestGeneric
crossref  |  CrossrefIntermediateSchema
crossref  |  CrossrefISSNList
crossref  |  CrossrefRawItems
crossref  |  CrossrefTask
crossref  |  CrossrefUniqISSNList
crossref  |  CrossrefUniqItems
dblp      |  DBLPDOIList
dblp      |  DBLPDownload
dblp      |  DBLPTask
default   |  DataciteCombine
default   |  DataciteExport
default   |  DataciteIntermediateSchema
default   |  DataciteTask
default   |  DefaultTask
default   |  MockTask
default   |  ZDBDownload
default   |  ZDBShortTitleMap
default   |  ZDBTask
dummy     |  DummyFail
dummy     |  DummyHelloWorld
dummy     |  DummyTask
highwire  |  HighwireCombine
highwire  |  HighwireExport
highwire  |  HighwireIntermediateSchema
highwire  |  HighwireTask
ieee      |  IEEEBacklogIntermediateSchema
ieee      |  IEEEBacklogPaths
ieee      |  IEEEDOIList
ieee      |  IEEEIntermediateSchema
ieee      |  IEEEPaths
ieee      |  IEEESolrExport
ieee      |  IEEETask
ieee      |  IEEEUpdatesIntermediateSchema
jstor     |  JstorCollectionMapping
jstor     |  JstorDOIList
jstor     |  JstorExport
jstor     |  JstorIntermediateSchema
jstor     |  JstorIntermediateSchemaGenericCollection
jstor     |  JstorISSNList
jstor     |  JstorLatestMembers
jstor     |  JstorMembers
jstor     |  JstorPaths
jstor     |  JstorTask
jstor     |  JstorXML
jstor     |  JstorXMLSlow
mag       |  MAGDates
mag       |  MAGDOIList
mag       |  MAGDump
mag       |  MAGFile
mag       |  MAGKeywordDistribution
mag       |  MAGPaperDomains
mag       |  MAGReferenceDB
mag       |  MAGTask
nl        |  DDNLPaths
nl        |  DDNLTask
nrw       |  NRWHarvest
nrw       |  NRWTask
nrw       |  NRWTransformation
oadoi     |  OADOIDump
oadoi     |  OADOIList
oadoi     |  OADOITask
pubmed    |  PubmedJournalList
pubmed    |  PubmedJournalListReduced
pubmed    |  PubmedMetadataPaths
pubmed    |  PubmedTask
springer  |  SpringerCleanFields
springer  |  SpringerCleanup
springer  |  SpringerDownload
springer  |  SpringerIntermediateSchema
springer  |  SpringerIssue11557
springer  |  SpringerPaths
springer  |  SpringerTask
wiso      |  Wiso2018Files
wiso      |  WisoTask
1         |  GutenbergDownload
1         |  GutenbergMARC
1         |  GutenbergTask
10        |  MTCHarvest
10        |  MTCMARC
10        |  MTCTask
13        |  DissonHarvest
13        |  DissonIntermediateSchema
13        |  DissonMARC
13        |  DissonTask
14        |  RISMDownload
14        |  RISMMARC
14        |  RISMTask
15        |  IMSLPConvert
15        |  IMSLPConvertDeprecated
15        |  IMSLPDownload
15        |  IMSLPDownloadDeprecated
15        |  IMSLPLegacyMapping
15        |  IMSLPTask
028       |  DOAJCSV
028       |  DOAJDOIList
028       |  DOAJDump
028       |  DOAJExport
028       |  DOAJFiltered
028       |  DOAJHarvest
028       |  DOAJIdentifierBlacklist
028       |  DOAJIntermediateSchema
028       |  DOAJISSNList
028       |  DOAJTask
30        |  SSOARExport
30        |  SSOARHarvest
30        |  SSOARIntermediateSchema
30        |  SSOARMARC
30        |  SSOARTask
34        |  PQDTCombine
34        |  PQDTExport
34        |  PQDTIntermediateSchema
34        |  PQDTTask
39        |  PerseeCombined
39        |  PerseeMARC
39        |  PerseeMARCIssue11349
39        |  PerseeTask
048       |  GeniosCombinedExport
048       |  GeniosCombinedIntermediateSchema
048       |  GeniosDatabases
048       |  GeniosDropbox
048       |  GeniosIntermediateSchema
048       |  GeniosISSNList
048       |  GeniosIssue10707Download
048       |  GeniosLatest
048       |  GeniosReloadDates
048       |  GeniosTask
50        |  DegruyterCombine
50        |  DegruyterDOIList
50        |  DegruyterExport
50        |  DegruyterIntermediateSchema
50        |  DegruyterISSNList
50        |  DegruyterPaths
50        |  DegruyterTask
50        |  DegruyterXML
52        |  OECDDownload
52        |  OECDMARC
52        |  OECDTask
53        |  CeeolJournalsDumpIntermediateSchema
53        |  CeeolTask
60        |  ThiemeCombine
60        |  ThiemeExport
60        |  ThiemeIntermediateSchema
60        |  ThiemeISSNList
60        |  ThiemeTask
70        |  EgyptologyFincMARC
70        |  EgyptologyTask
73        |  MarburgCombine
73        |  MarburgCombineNext
73        |  MarburgExport
73        |  MarburgIntermediateSchema
73        |  MarburgJSON
73        |  MarburgMarc
73        |  MarburgTask
78        |  IZIFincSolr
78        |  IZIIntermediateSchema
78        |  IZITask
80        |  DBInetFiles
80        |  DBInetIntermediateSchema
80        |  DBInetJSON
80        |  DBInetTask
085       |  ElsevierJournalsBacklogIntermediateSchema
085       |  ElsevierJournalsDOIList
085       |  ElsevierJournalsExport
085       |  ElsevierJournalsIntermediateSchema
085       |  ElsevierJournalsISSNList
085       |  ElsevierJournalsPaths
085       |  ElsevierJournalsTask
085       |  ElsevierJournalsUpdatesIntermediateSchema
87        |  IJOCFincSolr
87        |  IJOCHarvest
87        |  IJOCIntermediateSchema
87        |  IJOCTask
88        |  RUGMARC
88        |  RUGSpreadsheet
88        |  RUGTask
93        |  ZVDDHarvest
93        |  ZVDDIntermediateSchema
93        |  ZVDDTask
99        |  ZMPMARC
99        |  ZMPSpreadsheet
99        |  ZMPTask
100       |  MBPMARC
100       |  MBPSpreadsheet
100       |  MBPTask
101       |  KielFMFIntermediateSchema
101       |  KielFMFTask
103       |  MHLibraryHarvest
103       |  MHLibraryMARC
103       |  MHLibraryTask
107       |  HHBDCombine
107       |  HHBDExport
107       |  HHBDIntermediateSchema
107       |  HHBDTask
109       |  KHMDropbox
109       |  KHMIntermediateSchema
109       |  KHMLatest
109       |  KHMLatestDate
109       |  KHMTask
117       |  VKFilmBerlinMARC
117       |  VKFilmBerlinRawMARC
117       |  VKFilmBerlinTask
119       |  VKFilmFFFincMarc
119       |  VKFilmFFPaths
119       |  VKFilmFFTask
121       |  ArxivCombine
121       |  ArxivExport
121       |  ArxivIntermediateSchema
121       |  ArxivTask
124       |  DawsonDownload
124       |  DawsonExport
124       |  DawsonFixAndCombine
124       |  DawsonIntermediateSchema
124       |  DawsonTask
127       |  VKFilmFile
127       |  VKFilmMarc
127       |  VKFilmTask
133       |  CambridgeTask
141       |  LyndaDownload
141       |  LyndaIntermediateSchema
141       |  LyndaTask
143       |  JoveFincMARC
143       |  JoveIntermediateSchemaFromCSV
143       |  JoveMARC
143       |  JoveTask
148       |  VKFilmBAConvert
148       |  VKFilmBADownload
148       |  VKFilmBADownloadDeletions
148       |  VKFilmBADump
148       |  VKFilmBAMARC
148       |  VKFilmBATask
150       |  HSMWHarvest
150       |  HSMWMARC
150       |  HSMWTask
151       |  VKFilmBWDownload
151       |  VKFilmBWMARC
151       |  VKFilmBWTask
153       |  ArchiveDownload
153       |  ArchiveMARC
153       |  ArchiveSearch
153       |  ArchiveSearchMetadata
153       |  ArchiveTask
153       |  ArchiveTelevisionTexts
156       |  UMBIMARC
156       |  UMBITask
161       |  COAEBMARC
161       |  COAEBTask

