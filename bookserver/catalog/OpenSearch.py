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

class OpenSearch:
    namespace = 'http://a9.com/-/spec/opensearch/1.1/'

    def __init__(self, osddUrl):
        #OpenSearch Description Document URL
        self.osddUrl = osddUrl

    @classmethod
    def createTree(cls, xmlStr):
        """
        Creates element tree from OpenSearch description xml
        >>> e = OpenSearch.createTree(testXml)
        >>> print ET.tostring(e, pretty_print=True)
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
           <ShortName>Web Search</ShortName>
           <Description>Use Example.com to search the Web.</Description>
           <Tags>example web</Tags>
           <Contact>admin@example.com</Contact>
           <Url type="application/rss+xml" template="http://example.com/?q={searchTerms}&amp;pw={startPage?}&amp;format=rss"/>
        </OpenSearchDescription>
        
        """
        return ET.fromstring(xmlStr)
        
    @classmethod
    def selector(cls, tag):
        """
        Returns an ElementTree selector in the OpenSearch namespace
        >>> print OpenSearch.selector('ShortName')
        {http://a9.com/-/spec/opensearch/1.1/}ShortName
        """
        return '{%s}%s' % (cls.namespace, tag)
        
    @classmethod
    def getShortName(cls, tree):
        """
        >>> t = OpenSearch.createTree(testXml)
        >>> print OpenSearch.getShortName(t)
        Web Search
        """
        e = tree.findtext(cls.selector('ShortName'))
        return e
        



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
   <Url type="application/rss+xml" 
        template="http://example.com/?q={searchTerms}&amp;pw={startPage?}&amp;format=rss"/>
</OpenSearchDescription>
"""

    doctest.testmod()
    
if __name__ == "__main__":
    testmod()
    