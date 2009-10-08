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
sys.path.append("/petabox/www/bookserver")
import feedparser

import urlparse

from .. import Catalog
from .. import Entry
from .. import Navigation
from .. import OpenSearch
from .. import Link

class OpdsToCatalog():

    keymap = {'author': 'author',
     'author_detail': 'author_detail',
     'content': 'content',
     'dcterms_language': 'dcterms_language',
     'dcterms_publisher': 'dcterms_publisher',
     'id': 'urn',
     'links': 'links',
     'published': 'published',
     'published_parsed': 'published_parsed',
     'subtitle': 'subtitle',
     'title': 'title',
     'title_detail': 'title_detail',
     'updated': 'updated',
     'updated_parsed': 'updated_parsed'}

    # addNavigation()
    #___________________________________________________________________________        
    def addNavigation(self, c, f, url):
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

    # getCatalog()
    #___________________________________________________________________________    
    def getCatalog(self):        
        return self.c
            
    # OpdsToCatalog()
    #___________________________________________________________________________        
    def __init__(self, content, url):
        f = feedparser.parse(content)

        self.c = Catalog(title     = f.feed.title,
                    urn       = f.feed.id,
                    url       = url,
                    author    = f.feed.author,
                    authorUri = f.feed.author_detail.href,
                    datestr   = f.feed.updated,                                 
                   )

        self.addNavigation(self.c, f, url)

        for entry in f.entries:
            bookDict = dict( (OpdsToCatalog.keymap[key], val) for key, val in entry.iteritems() )
            links = []
            for l in entry.links:
                link = Link(url = l['href'], type = l['type'], rel = l['rel'])
                links.append(link)
            
            bookDict['content'] = bookDict['subtitle']
            self.removeKeys(bookDict, ('subtitle', 'updated_parsed', 'links', 'title_detail'))
            
            e = Entry(bookDict, links=links)
            self.c.addEntry(e)
            
            
if __name__ == '__main__':
    import doctest
    doctest.testmod()
