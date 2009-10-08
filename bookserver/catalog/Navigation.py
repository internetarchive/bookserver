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

class Navigation:

    @classmethod
    def getNext(self, start, numRows, numFound, urlBase):
        url   = None
        title = None

        if None == start:
            return url, title

        if (start+1)*numRows < numFound:
            title = 'Next results'
            url = '%s%d' % (urlBase, start+1)
    
        return url, title        

    @classmethod
    def getPrev(self, start, numRows, numFound, urlBase):
        url   = None
        title = None

        if None == start:
            return url, title

        if 0 != start:
            title = 'Prev results'
            url = '%s%d' % (urlBase, start-1)
    
        return url, title        

    @classmethod
    def initWithBaseUrl(cls, start, numRows, numFound, urlBase):
        (nextLink, nextTitle) = cls.getNext(start, numRows, numFound, urlBase)
        (prevLink, prevTitle) = cls.getPrev(start, numRows, numFound, urlBase)
        return cls(nextLink, nextTitle, prevLink, prevTitle)
    

    def __init__(self, nextLink, nextTitle, prevLink, prevTitle):
        self.nextLink  = nextLink
        self.nextTitle = nextTitle
        self.prevLink  = prevLink
        self.prevTitle  = prevTitle


if __name__ == '__main__':
    import doctest
    doctest.testmod()
        