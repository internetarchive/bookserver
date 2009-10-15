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


from Catalog    import Catalog
from Entry      import Entry
from Navigation import Navigation
from OpenSearch import OpenSearch
from Link       import Link

import ingest
import output

import time

def getCurrentDate():
    #If you are calling this function, you are probably fabricating an
    #atom:updated date because you don't know the actual atom:updated.        
    #A more legitimate use of this function is because your catalog is
    #continulously being updated (IA adds 2500 books/day). This function
    #changes the updated date every midnight, which might be more reasonable
    #than changing it continuously.
    t       = time.gmtime()
    datestr = time.strftime('%Y-%m-%dT%H:%M:%SZ', 
                (t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0))
    return datestr
