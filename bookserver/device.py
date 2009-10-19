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

import re

import catalog

class Device:
    name = "Generic device"


    def formatLink(self, link):
        """
        Formats a Link appropriately for device.
        """
        return link
                
class iPhone(Device):
    name = "iPhone and iPod Touch"

    def formatLink(self, link):
        """
        Does not copy object.
        >>> l = catalog.Link(url = 'http://www.archive.org/download/item.epub', type = 'application/epub+zip')
        >>> i = iPhone()
        >>> l = i.formatLink(l)
        >>> print l.get('url')
        epub://www.archive.org/download/item.epub
        """
        if 'application/epub+zip' == link.get('type'):
            newUrl = re.sub('^http', 'epub', link.get('url'))
            link.set('url', newUrl)
        return link
        
class Kindle(Device):
    name = 'Kindle'
    

class Detect:
    detectPatterns = {
        iPhone: [ 'Apple.*Mobile.*Safari' ],
        Kindle: [ 'Kindle/' ],
    }

    @classmethod
    def createFromUserAgent(cls, userAgent):
        """
        Return new instance of Device sub-class, or None
        >>> d = Detect.createFromUserAgent('Bogus')
        >>> print d
        None
        >>> d = Detect.createFromUserAgent('Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3')
        >>> print d.name
        iPhone and iPod Touch
        >>> d = Detect.createFromUserAgent('Mozilla/4.0 (compatible; Linux 2.6.10) NetFront/3.3 Kindle/1.0 (screen 600x800)')
        >>> print d.name
        Kindle
        """
        # $$$ list comprehension or reduce might be more efficient
        for device, patterns in cls.detectPatterns.items():
            for pattern in patterns:
                if re.search(pattern, userAgent):
                    return device() # return new instance
                    
        return None

                
if __name__ == "__main__":
    import doctest
    doctest.testmod()