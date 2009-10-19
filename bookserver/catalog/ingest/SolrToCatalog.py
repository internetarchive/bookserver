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
from ..Entry import IAEntry, Entry
from .. import Navigation
from .. import OpenSearch
from .. import Link
import bookserver.util.language

class SolrToCatalog:

    # map of solr field names to catalog key names
    # catalog key names that are plural are lists instead of strings
    keymap = {
              'identifier'     : 'identifier',
              'title'          : 'title',
              'date'           : 'date',
              'month'          : 'downloadsPerMonth',
              'price'          : 'price',
              'currencyCode'   : 'currencyCode',
              'provider'       : 'provider',
              'urn'            : 'urn',
              'summary'        : 'summary',
              'updated'        : 'updated',              
              
              #these are lists, not strings
              'creator'        : 'authors',
              'subject'        : 'subjects',
              'publisher'      : 'publishers',
              'language'       : 'languages',
              'contributor'    : 'contributors',
              'link'           : 'links',
              'rights'         : 'rights',
              
              'oai_updatedate' : 'oai_updatedates',
              'format'         : 'formats',

             }

    # removeKeys()
    #___________________________________________________________________________        
    def removeKeys(self, d, keys):
        for key in keys:
            d.pop(key, None)


    # entryFromSolrResult()
    #___________________________________________________________________________        
    def entryFromSolrResult(self, item, pubInfo):
        #use generator expression to map dictionary key names
        bookDict = dict( (SolrToCatalog.keymap[key], val) for key, val in item.iteritems() )

        links = []
        if 'price' in bookDict:
            if 0.0 == bookDict['price']:
                rel = 'http://opds-spec.org/acquisition'
                price = '0.00'
            else:
                price = str(bookDict['price'])
                rel = 'http://opds-spec.org/acquisition/buying'
        else:
            price = '0.00'
            rel = 'http://opds-spec.org/acquisition'

        if 'currencyCode' in bookDict:
            currencycode = bookDict['currencyCode']
        else:
            currencycode = 'USD'
        
        if not 'updated' in bookDict:
            #how did this happen?
            bookDict['updated'] = self.getDateString()
        
        for link in bookDict['links']:
            if link.endswith('.pdf'):
                l = Link(url  = link, type = 'application/pdf', 
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)
            elif link.endswith('.epub'):
                l = Link(url  = link, type = 'application/epub+zip', 
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)
            elif link.endswith('.mobi'):
                l = Link(url  = link, type = 'application/x-mobipocket-ebook', 
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)
            else:    
                l = Link(url  = link, type = 'text/html', 
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)

        if 'rights' in bookDict:
            rightsStr = ''
            for right in bookDict['rights']:
                #special case for Feedbooks
                if not '' == right:
                    rightsStr += right + ' '            
            if '' == rightsStr:
                self.removeKeys(bookDict, ('rights',))
            else:
                bookDict['rights'] = rightsStr
            
        self.removeKeys(bookDict, ('links','price', 'currencyCode')) 
        e = Entry(bookDict, links=links)

        return e

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
            if 0 == numFound:
                title += ' - no '
            else:
                title += ' - '
                if numRows > 0:
                    title += '%d to %d of ' % (start*numRows + 1, min((start+1)*numRows, numFound))
                title += "%d " % (numFound)
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

        osDescriptionDoc = pubInfo['opdsroot'] + '/opensearch.xml'
        o = OpenSearch(osDescriptionDoc)
        self.c.addOpenSearch(o)

        for item in obj['response']['docs']:
            entry = self.entryFromSolrResult(item, pubInfo)
            self.c.addEntry(entry)
  
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


# IASolrToCatalog()
#_______________________________________________________________________________
# The solr used for archive.org has a slightly different schema than the one
# recommended for a bookserver installation.

class IASolrToCatalog(SolrToCatalog):
    def entryFromSolrResult(self, item, pubInfo):
        #use generator expression to map dictionary key names
        bookDict = dict( (SolrToCatalog.keymap[key], val) for key, val in item.iteritems() )

        if 'oai_updatedate' in item:
            bookDict['updated'] = item['oai_updatedate'][-1] #this is sorted, get latest date
        else:
            bookDict['updated'] = self.getDateString()

        #IA scribe books use MARC language codes        
        if 'language' in item:
            bookDict['languages'] = []
            for lang in item['language']:
                bookDict['languages'].append(bookserver.util.language.iso_639_23_to_iso_639_1(lang))

        #special case: this is a result from the IA solr.
        #TODO: refactor this into a subclass IASolrToCatalog
        bookDict['urn'] = pubInfo['urnroot'] + ':item:' + item['identifier']

        pdfLink = Link(url  = "http://www.archive.org/download/%s/%s.pdf" % (item['identifier'], item['identifier']),
                       type = 'application/pdf', rel = 'http://opds-spec.org/acquisition')

        epubLink = Link(url  = "http://www.archive.org/download/%s/%s.epub" % (item['identifier'], item['identifier']),
                       type = 'application/epub+zip', rel = 'http://opds-spec.org/acquisition')
                                   
        e = IAEntry(bookDict, links=(pdfLink, epubLink))
        

        return e