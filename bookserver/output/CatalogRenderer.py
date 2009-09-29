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

# For pretty printing... since we don't have lxml
# from xml.dom.ext.reader import Sax2
# from xml.dom.ext import PrettyPrint
# from StringIO import StringIO
# 
# import xml.etree.ElementTree as ET

from lxml import etree as ET

class CatalogRenderer:

    # prettyPrintET()
    #______________________________________________________________________________
    def prettyPrintET(self, etNode):
        ### we have lxml now
        #reader = Sax2.Reader()
        #docNode = reader.fromString(ET.tostring(etNode))
        #tmpStream = StringIO()
        #PrettyPrint(docNode, stream=tmpStream)
        #return tmpStream.getvalue()
        
        return ET.tostring(etNode, pretty_print=True)
