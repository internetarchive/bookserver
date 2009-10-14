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

The OpdsToCatalog class takes a string with OPDS Atom data and returns
a Catalog instance.

See usage example in /test/OpdsToCatalog.txt
"""

import sys
sys.path.append("/petabox/sw/lib/python")
import feedparser

import urlparse

from .. import Catalog
from .. import Entry
from .. import Navigation
from .. import OpenSearch
from .. import Link

class OpdsToCatalog():

    keymap = {'author': 'authors',
     'author_detail': 'author_detail',
     'content': 'content',
     'dcterms_language': 'languages',
     'dcterms_publisher': 'publishers',
     'id': 'urn',
     'links': 'links',
     'published': 'date',
     'published_parsed': 'published_parsed',
     'subtitle': 'subtitle',
     'title': 'title',
     'title_detail': 'title_detail',
     'updated': 'updated',
     'updated_parsed': 'updated_parsed',
     'tags' : 'tags',
     'rights': 'rights',
     'summary_detail': 'summary_detail',
     'rights_detail': 'rights_detail',
     'summary':'summary',
     'dcterms_source':'dcterms_source',
     'href':'href',
     'link':'link',}

    # addNavigation()
    #___________________________________________________________________________        
    def addNavigation(self, c, f, url):
        if not 'links' in f.feed:
            return
            
        for link in f.feed.links:
            nextLink  = None
            nextTitle = None
            prevLink  = None
            prevTitle = None
            if 'next' == link.rel:
                nextLink  = urlparse.urljoin(url, link.href)
                nextTitle = link.title
            if 'prev' == link.rel:
                prevLink  = urlparse.urljoin(url, link.href)
                prevTitle = link.title

            if nextLink or prevLink:
                nav = Navigation(nextLink, nextTitle, prevLink, prevTitle)
                c.addNavigation(nav)

    # removeKeys()
    #___________________________________________________________________________        
    def removeKeys(self, d, keys):
        for key in keys:
            d.pop(key, None)

    # mergeTags()
    #   Feedparser's "tags" come from atom:category, and possibly other atom 
    #   elements. Our Category class uses 'subjects', which correspond with the
    #   the IA solr key name.
    #___________________________________________________________________________        
    def mergeTags(self, d):
        if 'tags' in d:
            if not 'subjects' in d:
                d['subjects'] = []
            
            for tag in d['tags']:
                d['subjects'].append(tag['term'])
            
            self.removeKeys(d, ('tags',))

    # scalarToList()
    #___________________________________________________________________________        
    def scalarToList(self, d, keys):
        for key in keys:
            if key in d:
                if not list == type(d[key]):
                    val = d[key]
                    d[key] = [val]

    # getCatalog()
    #___________________________________________________________________________    
    def getCatalog(self):        
        return self.c

    # specialCaseOReilly()
    #___________________________________________________________________________    
    def specialCaseOReilly(self, entry, links):
        if not 'content' in entry:
            return
        else:
            content = entry.content[0].value
            
        try:
            from lxml import html
            parser = html.fragment_fromstring(content)
            price = parser.xpath("//span[@class='price']")[0]
            if price.text.startswith('$'):
                priceVal = price.text.lstrip('$')
                currencyCode = 'USD'
                for link in links:
                    link.set('price', priceVal)
                    link.set('currencycode', currencyCode)
        except ImportError:
            pass
            

            
    # OpdsToCatalog()
    #___________________________________________________________________________        
    def __init__(self, content, url):
        f = feedparser.parse(content)

        authorUri = None
        if 'href' in f.feed.author_detail:
            authorUri = f.feed.author_detail.href
            
        self.c = Catalog(title     = f.feed.title,
                    urn       = f.feed.id,
                    url       = url,
                    author    = f.feed.author,
                    authorUri = authorUri,
                    datestr   = f.feed.updated,                                 
                   )

        self.addNavigation(self.c, f, url)

        for entry in f.entries:
            bookDict = dict( (OpdsToCatalog.keymap[key], val) for key, val in entry.iteritems() )
                                
            links = []
            for l in entry.links:
                link = Link(url = l['href'], type = l['type'], rel = l['rel'])
                links.append(link)

            if url.startswith('http://catalog.oreilly.com'):
                self.specialCaseOReilly(entry, links)
                
            self.mergeTags(bookDict)            
            
            #feedparser retuns both a content, which is a list of dicts,
            # and a subtitle, which is a string fabricated from atom:content
            # Remove the existing content, and replace with subtitle.
            if 'subtitle' in bookDict:
                bookDict['content'] = bookDict['subtitle']
            
            self.removeKeys(bookDict, ('subtitle', 'updated_parsed', 'links', 'title_detail', 'published_parsed', 'author_detail', 'summary_detail', 'rights_detail', 'href', 'link'))
            
            self.scalarToList(bookDict, ('languages','publishers', 'authors'))
            
            e = Entry(bookDict, links=links)
            self.c.addEntry(e)
            
            
if __name__ == '__main__':
    import doctest
    doctest.testmod()
