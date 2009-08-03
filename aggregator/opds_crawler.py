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

config = {'warc_dir':              '/crawler/data',
          'default_sleep_seconds': 5,  #TODO: set this per domain from robots.txt
          'max_warc_size':         100*1024*1024,
         }

feeds = (
         {'domain':'IA', 'url':'http://bookserver.archive.org/new', 'sorted_by_date':True},
         {'domain':'OReilly', 'url':'http://catalog.oreilly.com/stanza/new.xml', 'sorted_by_date':True},
        )

import feedparser #import feedparser before eventlet

from eventlet import coros, httpc, util

## From the eventlet examples page:
# replace socket with a cooperative coroutine socket because httpc
# uses httplib, which uses socket.  Removing this serializes the http
# requests, because the standard socket is blocking.
util.wrap_socket_with_coroutine_socket()

import os
import time
import glob
import re
import tempfile


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
def createNewWarc(domain, domain_warc_dir, tempdir):
    #Name the warc file based on the domain and crawl date
    warcDateTime = datetime.datetime.utcnow()

    warcFileName = '%s/%s_%s_warc.gz' % (domain_warc_dir, domain, warcDateTime.isoformat())
    print 'creating new warc file ' + warcFileName
    
    cmode = warc.WARC_FILE_COMPRESSED_GZIP
    
    w = WFile(warcFileName, config['max_warc_size'], warc.WARC_FILE_WRITER, cmode, tempdir)
    return w, warcFileName, warcDateTime

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


# crawlFeedRecursive()
#_______________________________________________________________________________
# fetches the feed, adds it to a warc (if necessary), updates solr, and then,
# if present, fetches the rel=next link
def crawlFeedRecursive(feed, url, crawlDateTime, latestWarc):

    data = httpc.get(url, headers = {"User-Agent": "Internet Archive OPDS Crawler +http://bookserver.archive.org",})
    print "%s fetched %s" % (time.asctime(), url)

    f     = feedparser.parse(data)
    t     = f.feed.updated_parsed
    dt    = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    delta = crawlDateTime - dt

    #if delta.days < 1:
    #     print 'feed update date less than one day since previous crawl'

    #TODO: make new warc if our warc file is too big
    #TODO: only add to warc if not already there.
    
    addToWarc(latestWarc, url, data, f, 'application/atom+xml')    

    time.sleep(config['default_sleep_seconds'])

    #recurse
    for link in f.feed.links:
        if 'next' == link['rel']:
            #feedparser automatically resolves relative links in link['href'],
            #but only if we have feedparser pull the url. We use httpc.get()
            #to pull the url, because we want to archive the raw data. Since
            #we call feedparser.parse() with a string and not a url, the 
            #url in link['href'] remains a relative url.
            
            starturl = feed['url']
            nexturl  = link['href']
            absurl = urlparse.urljoin(starturl, nexturl)
            crawlFeedRecursive(feed, str(absurl), crawlDateTime, latestWarc)


        
# crawlDomain()
#_______________________________________________________________________________
def crawlDomain(feed, crawlDateTime):
        
    
    print "%s fetching %s" % (time.asctime(), feed['domain'])
    
    domain_warc_dir = config['warc_dir'] + '/' + feed['domain']
    
    if not os.path.exists(domain_warc_dir):
        os.mkdir(domain_warc_dir, 0700)
    
    tempdir = tempfile.mkdtemp(prefix='opds-crawler-')
    print 'created tempdir ' + tempdir
    
    (latestWarc, warcFileName, warcDateTime) = getLatestWarc(domain_warc_dir, tempdir)    
    
    if None == latestWarc:
        (latestWarc, warcFileName, warcDateTime) = createNewWarc(feed['domain'], domain_warc_dir, tempdir)

    crawlFeedRecursive(feed, feed['url'], crawlDateTime, latestWarc)                       
     
    os.rmdir(tempdir)
    latestWarc.destroy()

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