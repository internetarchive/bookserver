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

class Catalog:

    """
    Catalog class init        
    """

    def __init__(self, 
                 title='Internet Archive OPDS',
                 urn='urn:x-internet-archive:bookserver:catalog',
                 url='https://bookserver.archive.org/catalog/',
                 datestr='1970-01-01T00:00:00Z',
                 author='Internet Archive',
                 authorUri='https://archive.org',
                 crawlableUrl=None
                ):
        self._authentication = None
        self._entries = []
        self._opensearch = None
        self._navigation = None
        self._title = title
        self._urn = urn
        self._url = url
        self._datestr = datestr
        self._author = author
        self._authorUri = authorUri
        self._crawlableUrl = crawlableUrl

    def addAuthentication(self, auth):
        self._authentication = auth

    def addEntry(self, entry):
        self._entries.append(entry)

    def addNavigation(self, nav):
        self._navigation = nav

    def addOpenSearch(self, opensearch):
        self._opensearch = opensearch

    def getEntries(self):
        return self._entries
