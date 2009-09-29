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

from CatalogRenderer import CatalogRenderer

import lxml.etree as ET
#import xml.etree.ElementTree as ET


class CatalogToAtom(CatalogRenderer):

    #some xml namespace constants
    #___________________________________________________________________________
    xmlns_atom    = 'http://www.w3.org/2005/Atom'
    xmlns_dc      = 'http://purl.org/dc/elements/1.1/'
    xmlns_dcterms = 'http://purl.org/dc/terms/'
    
    atom          = "{%s}" % xmlns_atom

    nsmap = {
                None:      xmlns_atom,
                'dc':      xmlns_dc,
                'dcterms': xmlns_dcterms,
            }
    
    # createTextElement()
    #___________________________________________________________________________
    def createTextElement(self, parent, name, value):
        element = ET.SubElement(parent, name)
        element.text = value
        return element
    
    # createRelLink()
    #___________________________________________________________________________
    def createRelLink(self, parent, rel, urlroot, relurl, title=None):
        absurl = urlroot + relurl
        element = ET.SubElement(parent, 'link')
        element.attrib['rel']  = rel
        element.attrib['type'] = 'application/atom+xml'
        element.attrib['href'] = absurl;
        if title:
            element.attrib['title'] = title;
        
    # createOpdsRoot()
    #___________________________________________________________________________
    def createOpdsRoot(self, title, urnroot, nss, urlroot, relurl, datestr, authorName, authorUri):
        ### TODO: add updated element and uuid element
        opds = ET.Element(CatalogToAtom.atom + "feed", nsmap=CatalogToAtom.nsmap)
        #opds.attrib['xmlns']         = 'http://www.w3.org/2005/Atom'
        #opds.attrib['xmlns:dc']      = 'http://purl.org/dc/elements/1.1/'
        #opds.attrib['xmlns:dcterms'] = 'http://purl.org/dc/terms/'
                    
        
        self.createTextElement(opds, 'title',    title)
        urn = urnroot + nss
        self.createTextElement(opds, 'id',       urn)
    
        self.createTextElement(opds, 'updated',  datestr)
        
        self.createRelLink(opds, 'self', urlroot, relurl)
        
        author = ET.SubElement(opds, 'author')
        self.createTextElement(author, 'name',  authorName)
        self.createTextElement(author, 'uri',   authorUri)
    
        #self.createRelLink(opds, 'search', '/opensearch.xml', 'Search ') # + author)
        return opds

    # createOpdsEntry()
    #___________________________________________________________________________
    def createOpdsEntry(self, opds, title, urn, url, datestr, content):
        entry = ET.SubElement(opds, 'entry')
        self.createTextElement(entry, 'title', title)
    
        #urn = 'urn:x-internet-archive:bookserver:' + nss
        self.createTextElement(entry, 'id',       urn)
    
        self.createTextElement(entry, 'updated',  datestr)
    
        element = ET.SubElement(entry, 'link')
        element.attrib['type'] = 'application/atom+xml'
        element.attrib['href'] = url;
        
        if content:
            self.createTextElement(entry, 'content',  content)

    # createOpenSearchDescription()
    #___________________________________________________________________________
    def createOpenSearchDescription(self, opds, opensearch):
        self.createRelLink(opds, 'search', opensearch.osddUrl, '', None)

    # __init__()
    #___________________________________________________________________________    
    def __init__(self, c):
        self.opds = self.createOpdsRoot(c._title, c._urnroot, ':', c._url, '/', c._datestr, c._author, c._authorUri)
        self.createOpenSearchDescription(self.opds, c._opensearch)

        for e in c._entries:
            self.createOpdsEntry(self.opds, e.get('title'), e.get('urn'), e.get('url'), e.get('datestr'), e.get('content'))
            
        
    # toString()
    #___________________________________________________________________________            
    def toString(self):
        return self.prettyPrintET(self.opds)

    # toElementTree()
    #___________________________________________________________________________    
    def toElementTree(self):
        return self.opds
        
        