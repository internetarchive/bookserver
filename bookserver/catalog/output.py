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

from Catalog import Catalog
from Entry import Entry
from OpenSearch import OpenSearch
from Navigation import Navigation
from Link  import Link

import lxml.etree as ET
import re

class CatalogRenderer:
    """Base class for catalog renderers"""

    def __init__(self):
        pass
        
    def toString(self):
        return ''
        
    def prettyPrintET(self, etNode):
        return ET.tostring(etNode, pretty_print=True)

class CatalogToAtom(CatalogRenderer):

    #some xml namespace constants
    #___________________________________________________________________________
    xmlns_atom    = 'http://www.w3.org/2005/Atom'
    xmlns_dc      = 'http://purl.org/dc/elements/1.1/'
    xmlns_dcterms = 'http://purl.org/dc/terms/'
    
    atom          = "{%s}" % xmlns_atom
    dcterms       = "{%s}" % xmlns_dcterms
    
    nsmap = {
        None     : xmlns_atom,
        'dc'     : xmlns_dc,
        'dcterms': xmlns_dcterms,
    }
    
    fileExtMap = {
        'pdf'  : 'application/pdf',
        'epub' : 'application/epub+zip'
    }
    
    ebookTypes = ('application/pdf',
                  'application/epub+zip')
    
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
    def createOpdsRoot(self, title, urn, urlroot, relurl, datestr, authorName, authorUri):
        ### TODO: add updated element and uuid element
        opds = ET.Element(CatalogToAtom.atom + "feed", nsmap=CatalogToAtom.nsmap)                    
        
        self.createTextElement(opds, 'title',    title)

        self.createTextElement(opds, 'id',       urn)
    
        self.createTextElement(opds, 'updated',  datestr)
        
        self.createRelLink(opds, 'self', urlroot, relurl)
        
        author = ET.SubElement(opds, 'author')
        self.createTextElement(author, 'name',  authorName)
        self.createTextElement(author, 'uri',   authorUri)
    
        #self.createRelLink(opds, 'search', '/opensearch.xml', 'Search ') # + author)
        return opds

    # createOpdsLink()
    #___________________________________________________________________________
    def createOpdsLink(self, entry, link):
        element = ET.SubElement(entry, 'link')
        element.attrib['href'] = link._url
        element.attrib['type'] = link._type
        if link._rel:
            element.attrib['rel']  = link._rel
    
    # createOpdsEntry()
    #___________________________________________________________________________
    def createOpdsEntry(self, opds, obj, links, fabricateContentElement):
        entry = ET.SubElement(opds, 'entry')
        self.createTextElement(entry, 'title', obj['title'])
    
        #urn = 'urn:x-internet-archive:bookserver:' + nss
        self.createTextElement(entry, 'id',       obj['urn'])
    
        self.createTextElement(entry, 'updated',  obj['updated'])
    
        downloadLinks = []
        for link in links:
            self.createOpdsLink(entry, link)
            if link._type in CatalogToAtom.ebookTypes:
                downloadLinks.append(link)
                    
        if 'date' in obj:
            element = self.createTextElement(entry, self.dcterms+'issued',  obj['date'][0:4])
    
        if 'authors' in obj:
            for author in obj['authors']:
                element = ET.SubElement(entry, 'author')
                self.createTextElement(element, 'name',  author)
                
        if 'subjects' in obj:
            for subject in obj['subjects']:
                element = ET.SubElement(entry, 'category')
                element.attrib['term'] = subject;
                
        if 'publishers' in obj: 
            for publisher in obj['publishers']:
                element = self.createTextElement(entry, self.dcterms+'publisher', publisher)
    
        if 'languages' in obj:
            for language in obj['languages']: 
                element = self.createTextElement(entry, self.dcterms+'language', language);
        
        if 'content' in obj:
            self.createTextElement(entry, 'content',  obj['content'])
        elif fabricateContentElement:
            ### fabricate an atom:content element if asked to
            ### FireFox won't show the content element if it contains nested html elements
            contentText=''
        
            if 'authors' in obj:
                if 1 == len(obj['authors']):
                    authorStr = '<b>Author: </b>'
                else:
                    authorStr = '<b>Authors: </b>'
                
                authorStr += ', '.join(obj['authors'])
                contentText += authorStr + '<br/>'
        
            #TODO: refactor
            if 'subjects' in obj:
                contentText += '<b>Subject </b>' + ', '.join(obj['subjects']) + '<br/>'
        
            if 'publishers' in obj:
                contentText += '<b>Publisher: </b>' + ', '.join(obj['publishers']) + '<br/>'
                
            if 'date' in obj:
                contentText += '<b>Year published: </b>' + obj['date'][0:4] + '<br/>'
        
            if 'contributors' in obj:
                contentText += '<b>Book contributor: </b>' + ', '.join(obj['contributors']) + '<br/>'
        
            if 'languages' in obj:
                contentText += '<b>Language: </b>' + ', '.join(obj['languages']) + '<br/>'
        
            if 'downloadsPerMonth' in obj:
                contentText += str(obj['downloadsPerMonth']) + ' downloads in the last month' + '<br/>'

            if len(downloadLinks):
                contentText += '<b>Download Ebook: </b>'
                for link in downloadLinks:
                    (start, sep, ext) = link._url.rpartition('.')
                    contentText += '(<a href="%s">%s</a>) '%(link._url, ext.upper())
        
            element = self.createTextElement(entry, 'content',  contentText)
            element.attrib['type'] = 'html'        

    # createOpenSearchDescription()
    #___________________________________________________________________________
    def createOpenSearchDescription(self, opds, opensearch):
        self.createRelLink(opds, 'search', opensearch.osddUrl, '', None)

    # createNavLinks()
    #___________________________________________________________________________
    def createNavLinks(self, opds, nav):        
        if nav.prevLink:
            self.createRelLink(opds, 'prev', '', nav.prevLink, nav.prevTitle)

        if nav.nextLink:
            self.createRelLink(opds, 'next', '', nav.nextLink, nav.nextTitle)

    # __init__()
    #___________________________________________________________________________    
    def __init__(self, c, fabricateContentElement=False):
        self.opds = self.createOpdsRoot(c._title, c._urn, c._url, '/', c._datestr, c._author, c._authorUri)

        if c._opensearch:
            self.createOpenSearchDescription(self.opds, c._opensearch)

        if c._navigation:
            self.createNavLinks(self.opds, c._navigation)

        for e in c._entries:
            self.createOpdsEntry(self.opds, e._entry, e._links, fabricateContentElement)
            
        
    # toString()
    #___________________________________________________________________________            
    def toString(self):
        return self.prettyPrintET(self.opds)

    # toElementTree()
    #___________________________________________________________________________    
    def toElementTree(self):
        return self.opds
        

class CatalogToHtml(CatalogRenderer):
    """
    The HTML page is organised thus:
        PageHeader
        Navigation
        Search
        CatalogHeader
        EntryList
        PageFooter
        
        >>> h = CatalogToHtml(testCatalog)
        >>> # print(h.toString())
    """
    
    entryDisplayKeys = [
        'authors',
        'date',
        'publishers',
        'contributors',
        'languages',
        'downloadsPerMonth'
    ]

    entryDisplayTitles = {
        'authors': ('Author', 'Authors'),
        'date': ('Published', 'Published'),
        'publishers': ( 'Publisher', 'Publishers'),
        'contributors': ('Contributor', 'Contributors'),
        'languages': ('Language', 'Languages'),
        'downloadsPerMonth': ('Recent downloads', 'Recent downloads'),
        'title': ('Title', 'Title')
    }
        
    entryLinkTitles = {
        'application/pdf': 'PDF',
        'application/epub': 'EPUB',
        'application/epub+zip': 'EPUB',
        'text/html': 'Online',
    }
        
    def __init__(self, catalog):
        CatalogRenderer.__init__(self)
        self.processCatalogToFragment(catalog) # XXX
        
    def processCatalog(self, catalog):
        html = self.createHtml(catalog)
        html.append(self.createHead(catalog))
        body = self.createBody(catalog)
        html.append(body)
        body.append(self.createHeader(catalog))
        body.append(self.createNavigation(catalog._navigation))
        body.append(self.createSearch(catalog._opensearch))
        body.append(self.createCatalogHeader(catalog))
        body.append(self.createEntryList(catalog._entries))
        body.append(self.createFooter(catalog))
        
        self.html = html
        return self

    def processCatalogToFragment(self, catalog):
        fragment = ET.Element('div', {'class':'opds-div'})
        fragment.append(self.createHeader(catalog))
        fragment.append(self.createNavigation(catalog._navigation))
        fragment.append(self.createSearch(catalog._opensearch))
        fragment.append(self.createCatalogHeader(catalog))
        fragment.append(self.createEntryList(catalog._entries))
        fragment.append(self.createFooter(catalog))
        
        self.html = fragment
        return self
        
    def createHtml(self, catalog):
        return ET.Element('html')
        
    def createHead(self, catalog):
        # XXX flesh out
        # updated
        # atom link
        
        head = ET.Element('head')
        titleElement = ET.SubElement(head, 'title')
        titleElement.text = catalog._title
        head.append(self.createStyleSheet('/static/catalog.css'))
        
        return head
            
    def createStyleSheet(self, url):
        """
        Returns a <link> element for the CSS stylesheet at given URL
        
        >>> l = testToHtml.createStyleSheet('/static/catalog.css')
        >>> ET.tostring(l)
        '<link href="/static/catalog.css" type="text/css" rel="stylesheet"/>'
        """
    
        # TODO add ?v={version}
        return ET.Element('link', {
            'rel':'stylesheet',
            'type':'text/css', 
            'href':url
        })
        
    def createBody(self, catalog):
        return ET.Element('body')
        
    def createHeader(self, catalog):
        div = ET.Element( 'div', {'class':'opds-header'} )
        div.text = 'OPDS Header' # XXX
        return div
        
    def createNavigation(self, navigation):
        """
        >>> start    = 5
        >>> numFound = 100
        >>> numRows  = 10
        >>> urlBase  = '/alpha/a/'
        >>> nav = Navigation.initWithBaseUrl(start, numRows, numFound, urlBase)
        >>> div = testToHtml.createNavigation(nav)
        >>> print ET.tostring(div)
        <div class="opds-navigation"><a href="/alpha/a/4.html" class="opds-navigation-anchor" rel="prev" title="Prev results">Prev results</a><a href="/alpha/a/6.html" class="opds-navigation-anchor" rel="next" title="Next results">Next results</a></div>
        """
        
        div = ET.Element( 'div', {'class':'opds-navigation'} )
        if not navigation:
            # No navigation provided, return empty div
            return div
                    
        # print '%s %s - %s %s' % (navigation.nextLink, navigation.nextTitle,
        #    navigation.prevLink, navigation.prevTitle)
            
        nextLink, nextTitle = navigation.nextLink, navigation.nextTitle
        prevLink, prevTitle = navigation.prevLink, navigation.prevTitle
        
        if (prevLink):
            prevA = self.createNavigationAnchor('prev', navigation.prevLink, navigation.prevTitle)
            div.append(prevA)
        else:
            # $$$ no further results, append appropriate element
            pass

        if (nextLink):
            nextA = self.createNavigationAnchor('next', navigation.nextLink, navigation.nextTitle)
            div.append(nextA)
        else:
            # $$$ no next results, append appropriate element
            pass
        
        return div
        
    def createNavigationAnchor(self, rel, url, title = None):
        """
        >>> a = testToHtml.createNavigationAnchor('next', 'a/1', 'Next results')
        >>> print ET.tostring(a)
        <a href="a/1.html" class="opds-navigation-anchor" rel="next" title="Next results">Next results</a>
        >>> a = testToHtml.createNavigationAnchor('prev', 'a/0.xml', 'Previous')
        >>> print ET.tostring(a)
        <a href="a/0.html" class="opds-navigation-anchor" rel="prev" title="Previous">Previous</a>
        """
        
        # Munge URL
        if url.endswith('.xml'):
            url = url[:-4]
        if not url.endswith('.html'):
            url += '.html'
        
        attribs = {'class':'opds-navigation-anchor',
            'rel': rel,
            'href': url}
        if title is not None:
            attribs['title'] = title    
        a = ET.Element('a', attribs)
        
        if title is not None:
            a.text = title
        return a
        
    def createSearch(self, opensearch):
        div = ET.Element( 'div', {'class':'opds-search'} )
        div.text = 'Search div' # XXX
        return div
        
    def createCatalogHeader(self, catalog):
        div = ET.Element( 'div', {'class':'opds-catalog-header'} )
        title = ET.SubElement(div, 'h1', {'class':'opds-catalog-header-title'} )
        title.text = catalog._title # XXX
        return div
                
    def createEntry(self, entry):
        """
        >>> e = testToHtml.createEntry(testEntry)
        >>> print ET.tostring(e)
        <p class="opds-entry"><h2 class="opds-entry-title">test item</h2><span class="opds-entry-item"><em class="opds-entry-key">Published:</em> <span class="opds-entry-value">1977</span><br/></span><span class="opds-entry-item"><em class="opds-entry-key">Download:</em> <a href="http://archive.org/details/itemid" class="opds-entry-link">http://archive.org/details/itemid</a></span></p>
        """
        
        e = ET.Element('p', { 'class':'opds-entry'} )
        title = ET.SubElement(e, 'h2', {'class':'opds-entry-title'} )
        title.text = entry.get('title')
        
        for key in self.entryDisplayKeys:
            value = entry.get(key)
            if value:
                displayTitle, displayValue = self.formatEntryValue(key, value)
                
                entryItem = ET.SubElement(e, 'span', {'class':'opds-entry-item'} )
                itemName = ET.SubElement(entryItem, 'em', {'class':'opds-entry-key'} )
                itemName.text = displayTitle + ':'
                itemName.tail = ' '
                itemValue = ET.SubElement(entryItem, 'span', {'class': 'opds-entry-value' } )
                itemValue.text = unicode(displayValue)
                ET.SubElement(entryItem, 'br')

        if entry._links:
            e.append(self.createEntryLinks(entry._links))
                                
        # TODO sort for display order
        # for key in Entry.valid_keys.keys():
        #    formattedEntryKey = self.createEntryKey(key, entry.get(key))
        #    if (formattedEntryKey):
        #        e.append( formattedEntryKey )
        
        return e
        
    def formatEntryValue(self, key, value):
        if type(value) == type([]):
            if len(value) == 1:
                displayTitle = self.entryDisplayTitles[key][0]
                displayValue = value[0]
                               
            else:
                # Multiple items
                displayTitle = self.entryDisplayTitles[key][1]
                displayValue = ', '.join(value)
        else:
            # Single item
            displayTitle = self.entryDisplayTitles[key][0]
            displayValue = value
            if 'date' == key:
                displayValue = displayValue[:4]

        return (displayTitle, displayValue)

    def createEntryLinks(self, links):
        """
        >>> pdf = Link(url = 'http://a.o/item.pdf', type='application/pdf')
        >>> epub = Link(url = 'http://a.o/item.epub', type='application/epub+zip')
        >>> links = [pdf, epub]
        >>> e = testToHtml.createEntryLinks(links)
        >>> print ET.tostring(e)
        <span class="opds-entry-item"><em class="opds-entry-key">Download:</em> <a href="http://a.o/item.pdf" class="opds-entry-link">PDF</a>, <a href="http://a.o/item.epub" class="opds-entry-link">EPUB</a></span>
        """
        s = ET.Element('span', { 'class':'opds-entry-item' } )
        title = ET.SubElement(s, 'em', {'class':'opds-entry-key'} )
        # $$$ TODO different formatting for different link types
        title.text = 'Download:'
        title.tail = ' '
        
        linkElems = [self.createEntryLink(link) for link in links]
        for linkElem in linkElems:
            s.append(linkElem)
            if linkElem != linkElems[-1]:
                linkElem.tail = ', '
        
        return s
        
    def createEntryLink(self, link):
        """
        >>> l = Link(url = 'http://foo.com/bar.pdf', type='application/pdf')
        >>> e = testToHtml.createEntryLink(l)
        >>> print ET.tostring(e)
        <a href="http://foo.com/bar.pdf" class="opds-entry-link">PDF</a>
        
        >>> l = Link(url = '/blah.epub', type='application/epub')
        >>> e = testToHtml.createEntryLink(l)
        >>> print ET.tostring(e)
        <a href="/blah.epub" class="opds-entry-link">EPUB</a>
        """
        
        if self.entryLinkTitles.has_key(link._type):
            title = self.entryLinkTitles[link._type]
        else:
            title = link._url
        
        a = ET.Element('a', {'class':'opds-entry-link',
            'href' : link._url
        })
        a.text = title
        return a
        
    def createEntryKey(self, key, value):
        # $$$ legacy
        
        if not value:
            # empty
            return None
        
        # XXX handle lists, pretty format key, order keys
        e = ET.Element('span', { 'class': 'opds-entry' })
        keyName = ET.SubElement(e, 'em', {'class':'opds-entry-key'})
        keyName.text = unicode(key, 'utf-8') + ':'
        keyName.tail = ' '
        keyValue = ET.SubElement(e, 'span', { 'class': 'opds-entry-value opds-entry-%s' % key })
        keyValue.text = unicode(value)
        ET.SubElement(e, 'br')
        return e
        
    def createEntryList(self, entries):
        list = ET.Element( 'ul', {'class':'opds-entry-list'} )
        for entry in entries:
            item = ET.SubElement(list, 'li', {'class':'opds-entry-list-item'} )
            item.append(self.createEntry(entry))
            list.append(item)
        return list
        
    def createFooter(self, catalog):
        div = ET.Element('div', {'class':'opds-footer'} )
        div.text = 'Page Footer Div' # XXX
        return div
        
    def toString(self):
        return self.prettyPrintET(self.html)
        
        
class ArchiveCatalogToHtml(CatalogToHtml):
    """
    Used to create an HTML catalog with Archive specific data and formatting
    """

    scandataRegex = re.compile('Scandata')

    def canReadOnline(self, entry):
        """
        Returns true if this item can be read in the online bookreader.
        """
        
        if not entry.get('identifier'):
            return False
        
        # Check for a readable format
        for format in entry.get('formats'):
            if self.scandataRegex.search(format):
                return True
            
        return False
    
    def readOnlineUrl(self, entry):
        return 'http://www.archive.org/stream/%s' % entry.get('identifier')
        
    
    def createEntry(self, entry):
        e = CatalogToHtml.createEntry(self, entry)
        identifier = entry.get('identifier')
        if identifier:
            s = ET.SubElement(e, 'span')
            ET.SubElement(s, 'br')
            a = ET.SubElement(s, 'a', {'href': 'http://www.archive.org/details/%s' % entry.get('identifier') })
            a.text = 'More information about this book'
            ET.SubElement(s, 'br')
            
            if self.canReadOnline(entry):
                s = ET.SubElement(s, 'span')
                a = ET.SubElement(s, 'a', {'href': self.readOnlineUrl(entry), 'title':'Read online'} )
                a.text = 'Read online'
                ET.SubElement(s, 'br')
                
        return e
        


def testmod():
    import doctest
    global testEntry, testCatalog, testToHtml
    
    urn = 'urn:x-internet-archive:bookserver:catalog'
    testCatalog = Catalog(title='Internet Archive OPDS', urn=urn)
    testLink    = Link(url  = 'http://archive.org/details/itemid',
                       type = 'application/atom+xml', rel='alternate')
    testEntry = Entry({'urn'  : 'x-internet-archive:item:itemid',
                        'title'   : u'test item',
                        'updated' : '2009-01-01T00:00:00Z',
                        'date': '1977-06-17T00:00:55Z'},
                        links=[testLink])
                        
    start    = 0
    numFound = 2
    numRows  = 1
    urlBase  = '/alpha/a/'
    testNavigation = Navigation.initWithBaseUrl(start, numRows, numFound, urlBase)
    testCatalog.addNavigation(testNavigation)
    
    osDescription = 'http://bookserver.archive.org/opensearch.xml'
    testSearch = OpenSearch(osDescription)
    testCatalog.addOpenSearch(testSearch)
    
    testCatalog.addEntry(testEntry)
    testToHtml = CatalogToHtml(testCatalog)
    
    doctest.testmod()
        
if __name__ == "__main__":
    testmod()
    
