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
                    
                

if __name__ == '__main__':
    import doctest
    doctest.testmod()
