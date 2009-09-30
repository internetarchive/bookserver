#!/usr/bin/env python

"""
Copyright(c)2008 Internet Archive. Software license AGPL version 3.

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

class CatalogRenderer:
    """Base class for catalog renderers"""

    def __init__(self):
        pass

    def render(self, catalog):
        """Returns the entire catalog rendered as a self-contained document as string"""
        return str(catalog)
        
    def renderCatalog(self, catalog):
        """Returns entire catalog rendered as string"""

    def renderEntry(self, entry):
        """Returns single entry as string"""
        return str(entry)
        
    def renderEntries(self, entryList):
        """Returns list of entries as string"""
        return str(entryList)
        
    def renderNavigation(self, navigation):
        """Returns navigation as string"""
        return str(navigation)
        
    def renderSearch(self, openSearch):
        """Returns search as string"""
        return str(openSearch)
        
    def prettyPrintET(self, etNode):
        return ET.tostring(etNode, pretty_print=True)
