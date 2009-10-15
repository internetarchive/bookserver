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

import lxml.etree as ET

import sys
sys.path.append("/petabox/sw/lib/python")

from opensearch.query import Query

class OpenSearch:
    namespace = 'http://a9.com/-/spec/opensearch/1.1/'
    atomXmlType = 'application/atom+xml'

    def __init__(self, osddUrl):
        #OpenSearch Description Document URL
        self.osddUrl = osddUrl

    @classmethod
    def createTree(cls, xmlStr):
        """
        Creates element tree from OpenSearch description xml
        >>> e = OpenSearch.createTree(testXml)
        >>> print ET.tostring(e, pretty_print=True).rstrip()
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
           <ShortName>Web Search</ShortName>
           <Description>Use Example.com to search the Web.</Description>
           <Tags>example web</Tags>
           <Contact>admin@example.com</Contact>
           <Url type="application/atom+xml" template="http://example.com/?q={searchTerms}&amp;pw={startPage?}"/>
        </OpenSearchDescription>
        
        """
        return ET.fromstring(xmlStr)
        
    @classmethod
    def selector(cls, tag):
        """
        Returns an xpath selector in the OpenSearch namespace
        >>> print OpenSearch.selector('ShortName')
        {http://a9.com/-/spec/opensearch/1.1/}ShortName
        """
        return '{%s}%s' % (cls.namespace, tag)

    @classmethod
    def getElements(cls, tree, tag, attribute = None, attributeValue = None):
        selector = 'os:%s' % tag
        if attribute:
            if attributeValue:
                selector += "[@%s='%s']" % (attribute, attributeValue)
            else:
                selector += "[@%s]" % attribute
                
        return tree.xpath(selector, namespaces = {'os': cls.namespace})
        
    @classmethod
    def getElement(cls, tree, tag, attribute = None, attributeValue = None):
        """
        >>> t = OpenSearch.createTree(testXml)
        >>> e = OpenSearch.getElement(t, 'Url', 'type', 'application/atom+xml')
        >>> print e.get('template')
        http://example.com/?q={searchTerms}&pw={startPage?}
        >>> n = OpenSearch.getElement(t, 'Url', 'type', 'application/atom+rss')
        >>> print n
        None
        """
        elements = cls.getElements(tree, tag, attribute, attributeValue)
        if elements and len(elements) >= 1:
            return elements[0]
        else:
            return None
            
    @classmethod
    def getText(cls, tree, tag, attribute = None, attributeValue = None):
        """
        >>> t = OpenSearch.createTree(testXml)
        >>> print OpenSearch.getText(t, 'ShortName')
        Web Search
        """
        e = cls.getElement(tree, tag, attribute, attributeValue)
        if e is not None:
            return e.text
        else:
            return ''
    
    @classmethod
    def getTemplate(cls, tree, type):
        """
        >>> t = OpenSearch.createTree(testXml)
        >>> print OpenSearch.getTemplate(t, OpenSearch.atomXmlType)
        http://example.com/?q={searchTerms}&pw={startPage?}
        """
        # $$$ deal with multiple urls
        e = cls.getElement(tree, 'Url', 'type', type)
        if e is not None:
            return e.get('template')
        else:
            raise ValueError('Could not find search template')
            
    @classmethod
    def createQuery(cls, template):
        """
        >>> q = OpenSearch.createQuery("http://example.com/?q={searchTerms}&pw={startPage?}")
        >>> q.searchTerms = 'foo bar'
        >>> q.startPage = 1
        >>> print q.url()
        http://example.com/?q=foo+bar&pw=1
        """
        q = Query(template)
        return q


def testmod():
    import doctest
    
    global testXml
    
    # From http://www.opensearch.org/Specifications/OpenSearch/1.1
    testXml = """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
   <ShortName>Web Search</ShortName>
   <Description>Use Example.com to search the Web.</Description>
   <Tags>example web</Tags>
   <Contact>admin@example.com</Contact>
   <Url type="application/atom+xml" 
        template="http://example.com/?q={searchTerms}&amp;pw={startPage?}"/>
</OpenSearchDescription>
"""

    doctest.testmod()
    
if __name__ == "__main__":
    testmod()
    