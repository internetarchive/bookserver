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

import sys
sys.path.append("/petabox/sw/lib/python")
import feedparser #for _parse_date()
import datetime
import string
import opensearch

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
    xmlns_dcterms = 'http://purl.org/dc/terms/'
    xmlns_opds    = 'http://opds-spec.org/'
    
    atom          = "{%s}" % xmlns_atom
    dcterms       = "{%s}" % xmlns_dcterms
    opdsNS        = "{%s}" % xmlns_opds
    
    nsmap = {
        None     : xmlns_atom,
        'dcterms': xmlns_dcterms,
        'opds'   : xmlns_opds
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
    def createOpdsRoot(self, c):
        ### TODO: add updated element and uuid element
        opds = ET.Element(CatalogToAtom.atom + "feed", nsmap=CatalogToAtom.nsmap)                    
        
        self.createTextElement(opds, 'title',    c._title)

        self.createTextElement(opds, 'id',       c._urn)
    
        self.createTextElement(opds, 'updated',  c._datestr)
        
        self.createRelLink(opds, 'self', c._url, '/')
        
        author = ET.SubElement(opds, 'author')
        self.createTextElement(author, 'name',  c._author)
        self.createTextElement(author, 'uri',   c._authorUri)
        
        if c._crawlableUrl:
            self.createRelLink(opds, 'http://opds-spec.org/crawlable', c._crawlableUrl, '', 'Crawlable feed')
            
        return opds

    # createOpdsLink()
    #___________________________________________________________________________
    def createOpdsLink(self, entry, link):
        element = ET.SubElement(entry, 'link')
        element.attrib['href'] = link.get('url')
        element.attrib['type'] = link.get('type')
        if link.get('rel'):
            element.attrib['rel']  = link.get('rel')
    
        if link.get('price'):
            price = self.createTextElement(element, CatalogToAtom.opdsNS+'price', link.get('price'))
            price.attrib['currencycode'] = link.get('currencycode')

        if link.get('formats'):
            for format in link.get('formats'):
                self.createTextElement(element, CatalogToAtom.dcterms+'hasFormat', format)
            
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
            if link.get('type') in CatalogToAtom.ebookTypes:
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
                    (start, sep, ext) = link.get('url').rpartition('.')
                    contentText += '(<a href="%s">%s</a>) '%(link.get('url'), ext.upper())
        
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
        CatalogRenderer.__init__(self)
        self.opds = self.createOpdsRoot(c)

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
        
    def __init__(self, catalog, device = None):
        CatalogRenderer.__init__(self)
        self.device = device
        self.processCatalog(catalog)
        
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
        div.text = 'Catalog Header' # XXX
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
        
    def createSearch(self, opensearchObj):
        div = ET.Element( 'div', {'class':'opds-search'} )
        
        # load opensearch
        osUrl = opensearchObj.osddUrl
        desc = opensearch.Description(osUrl)
        template = desc.get_url_by_type('application/atom+xml').template # $$$ error handling!
        
        form = ET.SubElement(div, 'form', {'class':'opds-search-form', 'action':'/search', 'method':'get' } ) # XXX should be relative
        ET.SubElement(form, 'br')
        ET.SubElement(form, 'input', {'class':'opds-search-template', 'type':'hidden', 'name':'t', 'value': template } )
        terms = ET.SubElement(form, 'input', {'class':'opds-search-terms', 'type':'text', 'name':'q' } )
        submit = ET.SubElement(form, 'input', {'class':'opds-search-submit', 'type':'submit', 'value':'Search'} )
        form.text = desc.shortname
        
        # XXX finish implementation
        
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
        
        if self.device:
            link = self.device.formatLink(link)
        
        if self.entryLinkTitles.has_key(link.get('type')):
            title = self.entryLinkTitles[link.get('type')]
        else:
            title = link.get('url')
        
        a = ET.Element('a', {'class':'opds-entry-link',
            'href' : link.get('url')
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

    def createHead(self, catalog):
        head = CatalogToHtml.createHead(self, catalog)
        # head.append(self.createStyleSheet('/static/ol.css'))
        return head
        
    def createHeader(self, catalog):
        div = ET.Element( 'div', {'class':'opds-header'} )
        ET.SubElement(div, 'img', {'src':'http://upstream.openlibrary.org/static/upstream/images/logo_OL-lg.png'})
        return div
    
    
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

    def createFooter(self, catalog):
        html = """
       <div id="bottom">
        <div id="legal">
        <p>Open Library is an initiative of the <a href="http://www.archive.org/">Internet Archive</a>, a 501(c)(3) non-profit, building a digital library of Internet sites and other cultural artifacts in digital form.<br/>

        Other projects include the <a href="http://web.archive.org/collections/web.html">Wayback Machine</a>, <a href="http://www.archive.org/">archive.org</a>, <a href="http://www.nasaimages.org/">nasaimages.org</a>, <a href="http://www.archive-it.org">archive-it.org</a>.</p>
        <p>Your use of the Open Library is subject to the Internet Archive's <a href="http://www.archive.org/about/terms.php">Terms of Use</a>.</p>
        </div>
       </div>
"""
        div = ET.fromstring(html)
        return div


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
        

#_______________________________________________________________________________
        
class CatalogToSolr(CatalogRenderer):
    '''
    Creates xml that can be sent to a Solr POST command
    '''

    def isEbook(self, entry):
        for link in entry.getLinks():            
            if 'application/pdf' == link.get('type'):
                return True
            elif 'application/epub+zip' == link.get('type'):
                return True
            elif 'application/x-mobipocket-ebook' == link.get('type'):
                return True
            elif ('buynow' == link.get('rel')) and ('text/html' == link.get('type')):
                #special case for O'Reilly Stanza feeds
                return True

        return False            

    def addField(self, element, name, data):
        field = ET.SubElement(element, "field")
        field.set('name', name)
        field.text=data        

    def addList(self, element, name, data):
        for scalar in data:
            self.addField(element, name, scalar)

    def makeSolrDate(self, datestr):
        """
        Solr is very particular about the date format it can handle
        """
        d = feedparser._parse_date(datestr)
        date = datetime.datetime(d.tm_year, d.tm_mon, d.tm_mday, d.tm_hour, d.tm_min, d.tm_sec)
        return date.isoformat()+'Z'
        
        
    def addEntry(self, entry):
        """
        Add each ebook as a Solr document
        """
        
        if not self.isEbook(entry):
            return
            
        doc = ET.SubElement(self.solr, "doc")
        self.addField(doc, 'urn',       entry.get('urn'))
        self.addField(doc, 'provider',  self.provider)      
        self.addField(doc, 'title',     entry.get('title'))
        
        self.addList(doc, 'creator',    entry.get('authors'))
        self.addList(doc, 'language',   entry.get('languages'))
        self.addList(doc, 'publisher',  entry.get('publishers'))
        self.addList(doc, 'subject',    entry.get('subjects'))
        
        self.addField(doc, 'updatedate', self.makeSolrDate(entry.get('updated')))

        if entry.get('summary'):
            self.addField(doc, 'description',     entry.get('summary'))
        
        if entry.get('date'):
            try:
                date = datetime.datetime(int(entry.get('date')), 1, 1)
                self.addField(doc, 'date', date.isoformat()+'Z')
            except ValueError:
                print """Can't make datetime from """ + entry.get('date')

        if entry.get('title'):
            try:
                self.addField(doc, 'firstTitle',  entry.get('title').lstrip(string.punctuation)[0].upper())
            except IndexError:
                print """Can't make firstTitle from """ + entry.get('title')
            self.addField(doc, 'titleSorter', entry.get('title').lstrip(string.punctuation).lower())

        #TODO: deal with creatorSorter, languageSorter

        price = None            #TODO: support multiple prices for different formats
        currencyCode = None
        for link in entry.getLinks():            
            if 'application/pdf' == link.get('type'):
                self.addField(doc, 'format', 'pdf')
                self.addField(doc, 'link',   link.get('url'))
                if link.get('price'):
                    price = link.get('price')
                    currencyCode = link.get('currencycode')
            elif 'application/epub+zip' == link.get('type'):
                self.addField(doc, 'format', 'epub')
                self.addField(doc, 'link',   link.get('url'))
                if link.get('price'):
                    price = link.get('price')
                    currencyCode = link.get('currencycode')
            elif 'application/x-mobipocket-ebook' == link.get('type'):
                self.addField(doc, 'format', 'mobi')
                self.addField(doc, 'link',   link.get('url'))
                if link.get('price'):
                    price = link.get('price')
                    currencyCode = link.get('currencycode')
            elif ('buynow' == link.get('rel')) and ('text/html' == link.get('type')):
                #special case for O'Reilly Stanza feeds
                self.addField(doc, 'format', 'shoppingcart')
                self.addField(doc, 'link',   link.get('url'))
                if link.get('price'):
                    price = link.get('price')
                    currencyCode = link.get('currencycode')

        if price:
            if not currencyCode:
                currencyCode = 'USD'
        else:
            price = '0.00'
            currencyCode = 'USD'
        
        self.addField(doc, 'price', price)
        self.addField(doc, 'currencyCode', currencyCode)
        ### old version of lxml on the cluster does not have lxml.html package
        #if 'OReilly' == self.provider: 
        #    content = html.fragment_fromstring(entry.get('content'))
        #    price = content.xpath("//span[@class='price']")[0]
        #    self.addField(doc, 'price', price.text.lstrip('$'))
        #elif ('IA' == self.provider) or ('Feedbooks' == self.provider):
        #    self.addField(doc, 'price', '0.00')


    def createRoot(self):
        return ET.Element("add")
    
    def __init__(self, catalog, provider):
        CatalogRenderer.__init__(self)
        self.provider = provider
        
        self.solr = self.createRoot()

        for entry in catalog.getEntries():
            self.addEntry(entry)

    def toString(self):
        return self.prettyPrintET(self.solr)
        
#_______________________________________________________________________________

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
    
