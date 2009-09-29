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

>>> import catalog
>>> c = catalog.Catalog()

>>> d = {'urn': 'x-internet-archive:item:itemid'}
>>> e = catalog.Entry(d)
>>> c.addEntry(e)

>>> nexturl = 'http://bookserver.archive.org/catalog/alpha/a/1'
>>> prevurl = None
>>> n = catalog.Navigation(nexturl, prevurl)
>>> c.addNavigation(n)

>>> osDescription = 'http://bookserver.archive.org/opensearch.xml'
>>> o = catalog.OpenSearch(osDescription)
>>> c.addOpenSearch(o)

"""

"""
bookserver/
    __init__.py
    
    catalog/
        __init__.py
        Catalog.py
        Entry.py
        Navigation.py
        OpenSearch.py
    
    ingest/
        __init__.py
        SolrToCatalog.py
        AtomToCatalog.py (future)

    output/
        __init__.py
        CatalogRenderer.py
        CatalogToXml.py
        CatalogToHtml.py
        CatalogToJson.py


>>> import bookserver.catalog as catalog
>>> c = catalog.Catalog()

>>> d = {'urn': 'x-internet-archive:item:itemid'}
>>> e = catalog.Entry(d)
>>> c.addEntry(e)

>>> nexturl = 'http://bookserver.archive.org/catalog/alpha/a/1'
>>> prevurl = None
>>> n = catalog.Navigation(nexturl, prevurl)
>>> c.addNavigation(n)

>>> osDescription = 'http://bookserver.archive.org/opensearch.xml'
>>> o = catalog.OpenSearch(osDescription)
>>> c.addOpenSearch(o)

>>> r = CatalogToXml()
>>> r.render(c)

"""

if __name__ == '__main__':
    import doctest
    doctest.testmod()
