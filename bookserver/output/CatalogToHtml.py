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

from CatalogRenderer import CatalogRenderer

import lxml.etree as ET

class CatalogToHtml(CatalogRenderer):
    
    def __init__(self, catalog):
        CatalogRenderer.__init__(self)
        self.processCatalog(catalog)
        
    def processCatalog(self, catalog):
        html = self.createHtml(catalog)
        html.append(self.createHead(catalog))
        body = self.createBody(catalog)
        html.append(body)
        
        # XXX
        #   nav
        #   opensearch
        body.append(self.createEntryList(catalog._entries))
        
        self.html = html
        return self
        
    def createHtml(self, catalog):
        return ET.Element('html')
        
    def createBody(self, catalog):
        return ET.Element('body')
        
    def createHead(self, catalog):
        # XXX flesh out
        # updated
        # atom link
        
        head = ET.Element('head')
        titleElement = ET.SubElement(head, 'title')
        titleElement.text = catalog._title
        
        return head
        
    def createEntry(self, entry):
        e = ET.Element('p')
        e.set('class', 'entry')
        title = ET.SubElement(e, 'h2')
        title.set('class', 'entryTitle')
        title.text = entry.get('title')
        
        # XXX other entryfields
        
        return e
        
    def createEntryList(self, entries):
        list = ET.Element('ul')
        list.set('class', 'entryList')
        for entry in entries:
            item = ET.SubElement(list, 'li')
            item.set('class', 'entryListItem')
            item.append(self.createEntry(entry))
            list.append(item)
        return list
        
    def toString(self):
        return self.prettyPrintET(self.html)