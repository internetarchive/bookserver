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
sys.path.append("/petabox/sw/lib/python")
import simplejson as json

from .. import Catalog
from ..Entry import IAEntry
from .. import Navigation
from .. import OpenSearch
from .. import Link

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
              'format'         : 'formats',

             }

    # SolrToCatalog()
    #___________________________________________________________________________    
    def __init__(self, pubInfo, url, urn, start=None, numRows=None, urlBase=None, titleFragment=None):
                    
        self.url = url
        f = urllib.urlopen(self.url)
        contents = f.read()
        f.close()
        obj = json.loads(contents)

        numFound = int(obj['response']['numFound'])
        
        title = pubInfo['name'] + ' Catalog'        

        if None != start:
            title += " - %d to %d of %d " % (start*numRows, min((start+1)*numRows, numFound), numFound)
        elif None != titleFragment:
            title += " - "
            
        if None != titleFragment:
            title += titleFragment
            
        self.c = Catalog(title     = title,
                         urn       = urn,
                         url       = pubInfo['opdsroot'],
                         author    = pubInfo['name'],
                         authorUri = pubInfo['uri'],
                         datestr   = self.getDateString(),                                 
                        )


        nav = Navigation.initWithBaseUrl(start, numRows, numFound, urlBase)
        self.c.addNavigation(nav)

        osDescriptionDoc = 'http://bookserver.archive.org/catalog/opensearch.xml'
        o = OpenSearch(osDescriptionDoc)
        self.c.addOpenSearch(o)

        for item in obj['response']['docs']:
            #use generator expression to map dictionary key names
            bookDict = dict( (SolrToCatalog.keymap[key], val) for key, val in item.iteritems() )

            if 'oai_updatedate' in item:
                bookDict['updated'] = item['oai_updatedate'][-1] #this is sorted, get latest date

            bookDict['urn'] = pubInfo['urnroot'] + ':item:' + item['identifier']

            pdfLink = Link(url  = "http://www.archive.org/download/%s/%s.pdf" % (item['identifier'], item['identifier']),
                           type = 'application/pdf', rel = 'http://opds-spec.org/acquisition')

            epubLink = Link(url  = "http://www.archive.org/download/%s/%s.epub" % (item['identifier'], item['identifier']),
                           type = 'application/epub+zip', rel = 'http://opds-spec.org/acquisition')
                                       
            try:
                e = IAEntry(bookDict, links=(pdfLink, epubLink))
                self.c.addEntry(e)
            except (KeyError, ValueError):
                # invalid entry, don't add it
                pass
                
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
        
        