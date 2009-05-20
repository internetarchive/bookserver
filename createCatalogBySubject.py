#!/usr/bin/env python

#Copyright(c)2009 Internet Archive. Software license GPL version 3.

"""
This script creates a set of OPDS catalog files in Atom format from a CSV file.
"""

import csv
import os
import sys
import datetime
import codecs, cStringIO
import xml.etree.ElementTree as ET

# You can customize these:
pubInfo = {
    'name'  : 'Internet Archive',
    'uri'   : 'http://archive.org',
    'email' : 'info@archive.org' ,
    'title' : "Internet Archive's Online Catalog",
    'subtitle' : "Download and read all the public domain books on the Internet Archive"
}

csvfile  = 'prelinger.csv'
outdir   = 'catalog'

# UTF-8 wrappers for csv.reader
# From http://docs.python.org/library/csv.html#csv-examples
#______________________________________________________________________________
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self
        

# createTextElement()
#______________________________________________________________________________
def createTextElement(parent, name, value):
    element = ET.SubElement(parent, name)
    element.text = value

# createCatalogXml()
#______________________________________________________________________________
def createCatalogXml(pubInfo, updated, subject=None):
    ### TODO: add updated element and uuid element
    catalogXml = ET.Element("feed")
    
    title = pubInfo['title']
    if None != subject:
        title += ' - ' + subject
        
    createTextElement(catalogXml, "title",    title)
    createTextElement(catalogXml, "subtitle", pubInfo['subtitle'])
    createTextElement(catalogXml, "updated",  updated)
    
    author = ET.SubElement(catalogXml, "author")
    createTextElement(author, "name",  pubInfo['name'])
    createTextElement(author, "uri",   pubInfo['uri'])
    createTextElement(author, "email", pubInfo['email'])
    return catalogXml

# addCatalogEntry()
#______________________________________________________________________________
def addCatalogEntry(catalog, title, updated):
    entry = ET.SubElement(catalog, "entry")
    createTextElement(entry, "title",  title)

    href = 'subjects/' + title + '.xml'
    link = ET.SubElement(entry, "link", {'type': 'application/atom+xml', 'href': href})

    createTextElement(entry, "updated",  updated)

# addBookEntry()
#______________________________________________________________________________
def addBookEntry(catalog, id, author, title, description, updated, pubInfo):
    entry = ET.SubElement(catalog, "entry")
    createTextElement(entry, "title",  title)
    
    authorET = ET.SubElement(entry, "author")
    createTextElement(authorET, "name",  author)

    urnNID = pubInfo['name'].replace(' ', '-')
    urn    = 'urn:%s:%s' % (urnNID, id)
    createTextElement(entry, "id",  urn)
    
    href = 'http://www.archive.org/download/%s/%s.pdf' % (id, id)
    link = ET.SubElement(entry, "link", {'type': 'application/pdf', 'href': href})

    createTextElement(entry, "updated",  updated)


# writeXml()
#______________________________________________________________________________
# uses minidom to pretty print an ET Element
def writeXml(xml, path):
    txt = ET.tostring(xml)

    import xml.dom.minidom as minidom
    prettyXml = minidom.parseString(txt).toprettyxml().encode( "utf-8" )

    f = open(path, 'w')
    f.write(prettyXml)
    f.close()


# createIndexXml()
#______________________________________________________________________________    
# creates a top-level catalog file at outdir/subjects.xml
def createIndexXml(subjectSet, outdir, pubInfo, updated):
    subjectsXml = createCatalogXml(pubInfo, updated)
    for subject in subjectSet:
        addCatalogEntry(subjectsXml, subject, updated)

    writeXml(subjectsXml, outdir + '/subjects.xml')

# createSubjectXml()
#______________________________________________________________________________    
def createSubjectXml(csvfile, subject, outdir, pubInfo, updated):
    reader = UnicodeReader(open(csvfile, "rb"))
    reader.next()  #the first row is a header

    xml = createCatalogXml(pubInfo, updated, subject)

    for row in reader:
        (id, author, title, subjectStr, description) = row
        if '' == subjectStr:
            subjectStr = 'unclassified'
            
        subjects = subjectStr.split(';')
        for s in subjects:
            s = s.replace(' ', '_');
            if s == subject:
                addBookEntry(xml, id, author, title, description, updated, pubInfo)
                
    writeXml(xml, "%s/subjects/%s.xml" % (outdir, subject))


# main()
#______________________________________________________________________________
if not os.path.exists(csvfile):
    sys.exit('input csv file %s does not exist' % (csvfile))

if os.path.exists(outdir):
    sys.exit('output directory %s already exists' % (outdir))

os.mkdir(outdir)
os.mkdir(outdir+'/subjects')

#atom <updated> elements use ISO 8601 format for time
updated = datetime.datetime.utcnow().isoformat()

reader = csv.reader(open(csvfile, "rb"))
reader.next() #the first row is a header

subjectSet = set()


for row in reader:
    (id, author, title, subjectStr, description) = row
    if '' == subjectStr:
        subjectStr = 'unclassified'
        
    subjects = subjectStr.split(';')
    for subject in subjects:
        subject = subject.replace(' ', '_');
        subjectSet.add(subject)


createIndexXml(subjectSet, outdir, pubInfo, updated)

for subject in subjectSet:
    createSubjectXml(csvfile, subject, outdir, pubInfo, updated)


