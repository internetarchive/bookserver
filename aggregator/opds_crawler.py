#!/usr/bin/python

'''
Copyright(c)2009 Internet Archive. Software license AGPL version 3.

This file is part of IA Bookserver.

    IA Bookserver is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    IA Bookserver is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with IA Bookserver.  If not, see <http://www.gnu.org/licenses/>.
    
'''    

'''
This is a very simple crawler for OPDS feeds.

It fetches one feed per provider, and pages through each feed using rel=next links.

It stores the fetched data in warc files, and addes new books to a solr search engine.
'''

# Configuration
#_______________________________________________________________________________

config = {'warc_dir':              '/2/crawler/data',
          'default_sleep_seconds': 5,  #TODO: set this per domain from robots.txt
          'max_warc_size':         1000*1024*1024,
         }

#sorted_by_date is to enable early-exit of the crawl.

feeds = (
         {'domain':'IA', 'url':'http://bookserver.archive.org/catalog/crawlable', 'sorted_by_date':False},
         #{'domain':'OReilly', 'url':'http://catalog.oreilly.com/stanza/alphabetical.xml', 'sorted_by_date':False},
         #{'domain':'Feedbooks', 'url':'http://www.feedbooks.com/discover/authors.atom', 'sorted_by_date':False},
        )
        

import feedparser #import feedparser before eventlet

from eventlet import coros, httpc, util

## From the eventlet examples page:
# replace socket with a cooperative coroutine socket because httpc
# uses httplib, which uses socket.  Removing this serializes the http
# requests, because the standard socket is blocking.
util.wrap_socket_with_coroutine_socket()

import commands
import os
import time
import glob
import re
import tempfile
import Queue
import string

import datetime
import xml.utils.iso8601
import time

import socket
import urlparse

import sys
sys.path.insert (0, "/usr/local/warc-tools/python/")
import warc
from   wfile   import WFile
from   wrecord import WRecord 

from   lxml    import etree, html


#writeLockFile()
#_______________________________________________________________________________
def writeLockFile(warc_dir):
    lockfile = warc_dir + '/lock'
    assert not os.path.exists(lockfile)
    f = open(lockfile, 'w')
    assert f
    f.close()

#rmLockFile()
#_______________________________________________________________________________
def rmLockFile(warc_dir):
    os.remove(warc_dir + '/lock')

#getLatestWarc()
#_______________________________________________________________________________
def getLatestWarc(domain_warc_dir, tempdir):

    warcs = sorted(glob.glob(domain_warc_dir + '/*_warc.gz'))
    if [] == warcs:
        print 'No warc file found in ' + domain_warc_dir
        return None, None, None
    else:
        warcFileName = warcs[-1]
        m = re.match(r"(\S+)_(\S+)_warc.gz", warcFileName)
        assert None != m
        
        isodate = xml.utils.iso8601.parse(m.group(2) + '+00:00')
        warcDateTime = datetime.datetime.utcfromtimestamp(isodate)
        
        cmode = warc.WARC_FILE_COMPRESSED_GZIP
    
        w = WFile(warcFileName, config['max_warc_size'], warc.WARC_FILE_WRITER, cmode, tempdir)
        
        return w, warcFileName, warcDateTime        

#createNewWarc()
#_______________________________________________________________________________
def createNewWarc(domain, domain_warc_dir, tempdir, crawlDateTime):
    
    #Name the warc file based on the domain and the date of the last update date
    #Since this is a new warc, we will use 01-01-1970 as update date. It will
    #get renamed with the crawl is finished to whatever is the lastest update
    #date in the feed
    
    ### We are now creating a new warc everytime, instead of adding to old ones
    #warcDateTime = datetime.datetime(1970, 1, 1, 0, 0, 0)
    warcDateTime = crawlDateTime

    warcFileName = '%s/%s_%s_warc.gz' % (domain_warc_dir, domain, warcDateTime.isoformat())
    print 'creating new warc file ' + warcFileName
    
    cmode = warc.WARC_FILE_COMPRESSED_GZIP
    
    w = WFile(warcFileName, config['max_warc_size'], warc.WARC_FILE_WRITER, cmode, tempdir)
    return w, warcFileName, warcDateTime

#renameWarc()
#_______________________________________________________________________________
def renameWarc(warcFileName, domain, domain_warc_dir, latestDateTime):
    newFileName = '%s/%s_%s_warc.gz' % (domain_warc_dir, domain, latestDateTime.isoformat())
    os.rename(warcFileName, newFileName)

# urlInWarc()
#_______________________________________________________________________________
def urlInWarc(url, warcFileName, tempdir):
    w = WFile ( warcFileName, config['max_warc_size'], warc.WARC_FILE_READER, warc.WARC_FILE_DETECT_COMPRESSION, tempdir)

    #while (w.hasMoreRecords()) :
        #r = w.nextRecord()
        #print r.getTargetUri()

# addToWarc()
#_______________________________________________________________________________
def addToWarc(w, uri, data, f, mime):
    o  = urlparse.urlparse(uri)
    ip = socket.gethostbyname(o.hostname)

    r = WRecord()
    r.setRecordType(warc.WARC_RESOURCE_RECORD)
    r.setTargetUri(uri, len(uri)) 

    #warc-tools can't handle the updated date in the format '2009-04-07T05:12:50+02:00'   
    #r.setDate(str(f.feed.updated), len(str(f.feed.updated)))
    t       = f.feed.updated_parsed
    dt      = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    updated = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    r.setDate(updated, len(updated))
    
    r.setContentType(mime, len(mime))
    r.setRecordId(str(f.feed.id), len(str(f.feed.id)))
    r.setIpAddress(ip, len(ip))
    r.setContentFromString(data, len(data))
    
    w.storeRecord(r)
    r.destroy()

# addField()
#_______________________________________________________________________________
def addField(element, name, data):
    field = etree.SubElement(element, "field")
    field.set('name', name)
    field.text=data

# addField2()
#_______________________________________________________________________________
def addField2(element, name, feedElement, key):
    if feedElement.has_key(key):
        addField(element, name, feedElement[key])

# addToSolr()
#_______________________________________________________________________________
# add feed to solr search engine
def addToSolr(feed, f, tempdir):

    numBooks = 0
    root = etree.Element("add")
    for e in f.entries:
        doc = etree.SubElement(root, "doc")


        gotBook = False        
        for l in e.links:
            if 'application/pdf' == l.type:
                addField(doc, 'format', 'pdf')
                addField(doc, 'link',   l.href)
                gotBook = True
            elif 'application/epub+zip' == l.type:
                addField(doc, 'format', 'epub')
                addField(doc, 'link',   l.href)
                gotBook = True 
            elif ('buynow' == l.rel) and ('text/html' == l.type):
                #stanza-style link
                addField(doc, 'format', 'shoppingcart')
                addField(doc, 'link',   l.href)
                gotBook = True
            #else:
                #print 'skipping link: '
                #print l
                #print


        if not gotBook:
            continue
        else:
            numBooks += 1

        addField(doc, 'urn',          e.id)
        addField(doc, 'provider',     feed['domain'])        
        
        addField2(doc, 'title',       e, 'title')
        addField2(doc, 'creator',     e, 'author')
        addField2(doc, 'language',    e, 'language')
        addField2(doc, 'publisher',   e, 'publisher')

        #dates
        if e.has_key('updated_parsed'):
            d = e.updated_parsed
            date = datetime.datetime(d.tm_year, d.tm_mon, d.tm_mday, d.tm_hour, d.tm_min, d.tm_sec)
            addField(doc, 'updatedate', date.isoformat()+'Z')

        if e.has_key('published'):            
            date = datetime.datetime(int(e.published), 1, 1)
            addField(doc, 'date', date.isoformat()+'Z')
        
            
        if e.has_key('tags'):
            for t in e.tags:
                addField(doc, 'subject', t.term)
        
        # for O'Reilly stanza feeds, price is in <content>
        if 'OReilly' == feed['domain']: 
            content = html.fragment_fromstring(e.content[0].value)
            price = content.xpath("//span[@class='price']")[0]
            addField(doc, 'price', price.text.lstrip('$'))
        elif ('IA' == feed['domain']) or ('Feedbooks' == feed['domain']):
            addField(doc, 'price', '0.00')
        
        if e.has_key('title'):
            addField(doc, 'titleSorter', e.title.lstrip(string.punctuation)[0].upper())
        
        #TODO: deal with description, titleSorter, creatorSorter, languageSorter

    if numBooks:
        solr_import_xml = tempdir + "/solr_import.xml"
        tree = etree.ElementTree(root)
        tree.write(solr_import_xml)
        #print etree.tostring(tree, pretty_print=True);
        command = """/solr/example/exampledocs/post.sh '%s'""" % (solr_import_xml)
        
        (ret, out) = commands.getstatusoutput(command)
        if -1 == out.find('<int name="status">0</int>'):
            print out
        assert 0 == ret
        
        os.unlink(solr_import_xml)

# addToQueue()
#_______________________________________________________________________________
def addToQueue(nexturl, feedurl, queue):
    #feedparser automatically resolves relative links in link['href'],
    #but only if we have feedparser pull the url. We use httpc.get()
    #to pull the url, because we want to archive the raw data. Since
    #we call feedparser.parse() with a string and not a url, the 
    #url in link['href'] remains a relative url.

    absurl = urlparse.urljoin(feedurl, nexturl)
    queue.put(str(absurl))
    #print 'adding ' + absurl

# parseLinks()
#_______________________________________________________________________________
def parseLinks(f, feedurl, queue):
    if f.feed.has_key('links'):
        for link in f.feed.links:
            if 'next' == link['rel']:
                addToQueue(link['href'], feedurl, queue)

    dont_crawl=('related', 'replies')
    for e in f.entries:
        for l in e.links:
            if 'application/atom+xml' == l.type:
                if l.rel in dont_crawl:
                    continue;
                
                addToQueue(l.href, feedurl, queue)

# crawlFeedOnePage()
#_______________________________________________________________________________
# fetches the feed, adds it to a warc (if necessary), updates solr, and then,
# if present, fetches the rel=next link
def crawlFeedOnePage(feed, queue, crawlDateTime, latestWarc, warcDateTime, latestDateTime, tempdir):

    url = queue.get()
    print "<- %s fetching %s for domain %s" % (time.asctime(), url, feed['domain'])
    data = httpc.get(url, headers = {"User-Agent": "Internet Archive OPDS Crawler +http://bookserver.archive.org",})
    print "-> %s fetched %s for domain %s" % (time.asctime(), url, feed['domain'])

    f     = feedparser.parse(data)
    t     = f.feed.updated_parsed
    dt    = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    delta = crawlDateTime - dt

    #if delta.days < 1:
    #     print 'feed update date less than one day since previous crawl'

    #TODO: make new warc if our warc file is too big
    #TODO: only add to warc if not already there.

    ###turn off addToWarc while debugging
    #if (warcDateTime < dt):
    #    print "Feed updated date is newer than warc date. Adding to warc"
    if True:
        addToWarc(latestWarc, url, data, f, 'application/atom+xml')
        latestDateTime = dt

    #just archive, no longer feed solr from this script
    #addToSolr(feed, f, tempdir)

    parseLinks(f, feed['url'], queue)
    


    time.sleep(config['default_sleep_seconds'])

    return latestDateTime

# crawlDomain()
#_______________________________________________________________________________
def crawlDomain(feed, crawlDateTime):
        
    
    print "%s fetching %s" % (time.asctime(), feed['domain'])
    
    domain_warc_dir = config['warc_dir'] + '/' + feed['domain']
    
    if not os.path.exists(domain_warc_dir):
        os.mkdir(domain_warc_dir, 0700)
    
    tempdir = tempfile.mkdtemp(prefix='opds-crawler-')
    print 'created tempdir ' + tempdir
    
    ### Create a new warc everytime instead of adding to an old one
    #(latestWarc, warcFileName, warcDateTime) = getLatestWarc(domain_warc_dir, tempdir)    
    #
    #if None == latestWarc:
    #    (latestWarc, warcFileName, warcDateTime) = createNewWarc(feed['domain'], domain_warc_dir, tempdir)
    (latestWarc, warcFileName, warcDateTime) = createNewWarc(feed['domain'], domain_warc_dir, tempdir, crawlDateTime)

    queue = Queue.Queue() #a Queue might be overkill here; could probably use a list
    queue.put(feed['url'])
    
    while not queue.empty():
        latestDateTime = crawlFeedOnePage(feed, queue, crawlDateTime, latestWarc, warcDateTime, warcDateTime, tempdir)
    
    print "Finished crawling %s, whose feed was last updated on %s" % (feed['domain'], latestDateTime.isoformat())
        
    os.rmdir(tempdir)
    latestWarc.destroy()

    ### Create a new warc everytime instead of adding to an old one
    #renameWarc(warcFileName, feed['domain'], domain_warc_dir, latestDateTime)
    
# __main__
#_______________________________________________________________________________

assert os.path.exists(config['warc_dir'])    
writeLockFile(config['warc_dir'])

crawlDateTime = datetime.datetime.utcnow()
pool = coros.CoroutinePool(max_size=4)
waiters = []
for feed in feeds:
    waiters.append(pool.execute(crawlDomain, feed, crawlDateTime))
    

#wait until all feeds have been fetched
for waiter in waiters:
    waiter.wait()
    
rmLockFile(config['warc_dir'])    