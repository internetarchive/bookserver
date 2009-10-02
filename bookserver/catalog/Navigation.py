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

    def getNext(self, start, numRows, numFound, urlBase):
        url   = None
        title = None

        if None == start:
            return url, title

        if (start+1)*numRows < numFound:
            title = 'Next results'
            url = '%s%d' % (urlBase, start+1)
    
        return url, title        

    def getPrev(self, start, numRows, numFound, urlBase):
        url   = None
        title = None

        if None == start:
            return url, title

        if 0 != start:
            title = 'Prev results'
            url = '%s%d' % (urlBase, start-1)
    
        return url, title        

    
    def __init__(self, start, numRows, numFound, urlBase):
        (self.nextLink, self.nextTitle) = self.getNext(start, numRows, numFound, urlBase)
        (self.prevLink, self.prevTitle) = self.getPrev(start, numRows, numFound, urlBase)
        
if __name__ == '__main__':
    import doctest
    doctest.testmod()
        