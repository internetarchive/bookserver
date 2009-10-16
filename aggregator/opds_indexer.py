#!/usr/bin/env python

"""
Copyright(c)2009 Internet Archive. Software license AGPL version 3.

This file is part of bookserver.

    bookserver is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    bookserver is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with bookserver.  If not, see <http://www.gnu.org/licenses/>.

    The bookserver source is hosted at http://github.com/internetarchive/bookserver/

This file takes a WARC file as input, and adds all Atom contents to Solr.
"""

import sys
import tempfile
import os
import commands

sys.path.insert (0, "/usr/local/warc-tools/python/")
import warc
from   wfile   import WFile
from   wrecord import WRecord
from   wbloc   import WBloc

sys.path.append('..')
import bookserver

config = {'warc_dir':              '/2/crawler/data',
          'default_sleep_seconds': 5,  #TODO: set this per domain from robots.txt
          'max_warc_size':         1000*1024*1024,
         }

providers = (
         {'provider':'IA',        'url':'http://bookserver.archive.org'},
         {'provider':'OReilly',   'url':'http://catalog.oreilly.com'},
         {'provider':'Feedbooks', 'url':'http://www.feedbooks.com'},
        )

# getProvider
#______________________________________________________________________________
def getProvider(url):
    for d in providers:
        if url.startswith(d['url']):
            return d['provider']
    raise KeyError('no provider found for url %s' % (url))            

# indexWarc()
#   loop over the contents of a WARC file, and add them to solr
#______________________________________________________________________________
def indexWarc(warcFileName):
    tempdir = tempfile.mkdtemp(prefix='opds-crawler-')
    print 'created tempdir ' + tempdir

    w = WFile (warcFileName, config['max_warc_size'], warc.WARC_FILE_READER, warc.WARC_FILE_DETECT_COMPRESSION, tempdir)
    assert w

    while ( w.hasMoreRecords() ) :

        r = w.nextRecord()
        if None == r:
            w.destroy ()
            print "bad record.. bailing!"
            return
        
        url = r.getTargetUri()
        print 'processing ' + url
        b = WBloc (w, r, False, 64 * 1024)
        
        content = ''
        while True:
            buf = b.getNext()
            if buf:
                content += buf
                #sys.stdout.write(buf)
            else:
                break

        if 'application/atom+xml' == r.getContentType():
            ingestor = bookserver.catalog.ingest.OpdsToCatalog(content, url)
            c = ingestor.getCatalog()
            provider = getProvider(url)
            renderer = bookserver.catalog.output.CatalogToSolr(c, provider)
            str = renderer.toString()
            
            solr_import_xml = tempdir + "/solr_import.xml"
            f = open(solr_import_xml, 'w')
            f.write(str)
            f.close()
                        
            command = """/solr/example/exampledocs/post.sh '%s'""" % (solr_import_xml)
            
            (ret, out) = commands.getstatusoutput(command)
            if -1 == out.find('<int name="status">0</int>'):
                print out
            assert 0 == ret

            os.unlink(solr_import_xml)
            

        b.destroy()
        r.destroy()
        
    os.rmdir(tempdir)
    w.destroy()


# main
#______________________________________________________________________________

assert 2 == len(sys.argv)
warcFileName = sys.argv[1]

indexWarc(warcFileName)
