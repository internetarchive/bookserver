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
"""

import urllib
import time

import sys
sys.path.append("/petabox/www/bookserver")
import simplejson as json

from .. import Catalog
from .. import Entry

class SolrToCatalog:

    # map of solr field names to catalog key names
    # catalog key names that are plural are lists instead of strings
    keymap = {
              'identifier'     : 'identifier',
              'title'          : 'title',
              'date'           : 'date',
              'month'          : 'downloadsPerMonth',
              
              #these are lists, not strings
              'creator'        : 'authors',
              'subject'        : 'subjects',
              'publisher'      : 'publishers',
              'language'       : 'languages',
              'contributor'    : 'contributors',
              
              'oai_updatedate' : 'oai_updatedates',

             }

    # SolrToCatalog()
    #___________________________________________________________________________    
    def __init__(self, pubInfo, url):
        
        self.url = url
        f = urllib.urlopen(self.url)
        contents = f.read()
        f.close()
        obj = json.loads(contents)
        
        self.c = Catalog(title     = pubInfo['name'] + ' OPDS',
                                 urnroot   = pubInfo['urnroot'],
                                 url       = pubInfo['opdsroot'],
                                 author    = pubInfo['name'],
                                 authorUri = pubInfo['uri'],
                                 datestr   = self.getDateString(),                                 
                                )
        for item in obj['response']['docs']:
            #use generator expression to map dictionary key names
            bookDict = dict( (SolrToCatalog.keymap[key], val) for key, val in item.iteritems() )

            if 'oai_updatedate' in item:
                bookDict['updated'] = item['oai_updatedate'][-1] #this is sorted, get latest date

            bookDict['urn'] = pubInfo['urnroot'] + ':item:' + item['identifier']
            bookDict['url'] = "http://www.archive.org/download/%s/%s.pdf" % (item['identifier'], item['identifier'])
            
            e = Entry(bookDict)
            self.c.addEntry(e)
            #print bookDict
        
    # getCatalog()
    #___________________________________________________________________________    
    def getCatalog(self):        
        return self.c

    # getDateString()
    #___________________________________________________________________________
    def getDateString(self):
        #IA is continuously scanning books. Since this OPDS file is constructed
        #from search engine results, let's change the updated date every midnight
        t       = time.gmtime()
        datestr = time.strftime('%Y-%m-%dT%H:%M:%SZ', 
                    (t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0))
        return datestr
        
    def nextPage(self):        
        raise NotImplementedError

    def prevPage(self):        
        raise NotImplementedError
        
        