#!/usr/bin/env python

#Copyright(c)2009 Internet Archive. Software license GPL version 3.


import csv
import os
import sys
import urllib
import cStringIO
import codecs
import xml.etree.ElementTree as ET

# UTF-8 wrappers for csv.writer
# From http://docs.python.org/library/csv.html#csv-examples
# _____________________________________________________________________________
class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

# getString(ET.Element xml, string key)
# _____________________________________________________________________________
def getString(xml, key):
    element = xml.find(key)
    if None == element:
        return ""
    else:
        return element.text

# main()
# _____________________________________________________________________________

"""
List of identifiers for the Prelinger Collection was fetched from the following url:
http://www.archive.org/advancedsearch.php?q=collection%3Aprelinger_library&fl%5B%5D=identifier&sort%5B%5D=&sort%5B%5D=&sort%5B%5D=&rows=32000&fmt=csv&xmlsearch=Search
"""

ids = [
    "americanhealthse01charrich",
    "americanhealthse03charrich",
    "belltelephonevol2728mag00amerrich",
    "bellvol25telephonemag00amerrich",
    "bellvol36systemtechni00amerrich",
    "city00planbostvol2rich",
    "crabtreebasucser00crabrich",
    "descriptionofest00warrrich",
    "draftenvironmentunit00rich",
    "educationeconomi00educrich",
    "goldencruciblein00rossrich",
    "homebookofgreate00crderich",
    "indexoftrainingf00busirich",
    "kenilworthfirstf00kenirich",
    "krushchevreportc00meyerich",
    "midcountrywritin00wimbrich",
    "natural00resourcescalunitrich",
    "overlandmonthly37sanfrich",
    "plain00srockiesbibwagnrich",
    "planningcivilcom00washrich",
    "prairiepoets194900pasqrich",
    "radioindustrysto00harvrich",
    "roadtohealth00jonerich",
    "roadtooregonchro00ghenrich",
    "dunelandechoes00lakerich",
    "cityplan00bostrich",
    "californiablue1911bo00calirich",
    "bellvol35systemtechni00amerrich",
    "geographicbackgr00goodrich",
    "bellsystemtechni00amerrich",
    "bellvol24telephonemag00amerrich",
    "investigations1953of00unitrich",
    "modernartinstore00wmlirich",
    "eisvoliienvironment00unitrich",
    "marvelsofachieve00bassrich",
    "draftenvironment00unitrich",
    "birdsofvol2easternnocory00rich",
    "mainspringgrassr00weavrich",
    "report00ofnationalnatirich",
    "hearing1967beforeuni00unitrich",
    "birdsnaturemagaz00marbrich",
    "deathslamsdoor00caderich",
    "bluebookofaudiov00chicrich",
    "youareallalone00kovrich",
    "healthgrowthseri00charrich",
    "americanhealthse02charrich",
    "sanitation00physioritcrich",
    "howsocialismwork00strarich",
    "aztecruinsnation00listrich",
    "preliminaryrepor00iowarich",
    "pr00acticalchildtrbeerrich",
    "wouldcommunismwo00crosrich",
    "structuralindust00auburich",
    "bellsystemtechni02amerrich",
    "birds00ofeasternnovol1coryrich",
    "factfancyintnecm00scovrich",
    "bellvol7systemtechni00amerrich",
    "wall00ofmenrollrich",
    "hightreasonplota00kahnrich",
    "humanengineering00wintrich",
    "youcantdothat00seldrich",
    "bellsystemtechni01amerrich"
]

csvfile = 'prelingerOut.csv'

if os.path.exists(csvfile):
    sys.exit('output csv file %s already exists' % (csvfile))
    
#outcsv = csv.writer(open(csvfile, 'w'))
outcsv = UnicodeWriter(open(csvfile, 'w'))

#write csv header line
outcsv.writerow(["barcode","author","title","subject","description"])

for id in ids:
    print id
    url     = 'http://www.archive.org/download/%s/%s_meta.xml' % (id, id)
    content = urllib.urlopen(url).read()
    metaXml = ET.fromstring(content)
    
    author = getString(metaXml, 'creator')
    title = getString(metaXml, 'title')
    description = getString(metaXml, 'description')
    
    subjects = metaXml.findall('subject')
    
    subject = ''
    numSubjects = len(subjects)
    for i in range(0, numSubjects):
        subject += subjects[i].text.replace(';','-')
        if i != (numSubjects-1):
            subject += ';'

    outcsv.writerow([id, author, title, subject, description])
    