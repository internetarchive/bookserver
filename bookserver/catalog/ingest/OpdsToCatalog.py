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

The OpdsToCatalog class takes a string with OPDS Atom data and returns
a Catalog instance.
"""

"""
>>> import urllib
>>> url = 'http://bookserver.archive.org/catalog/'
>>> fh = urllib.urlopen(url)
>>> content = fh.read()
>>> fh.close()
>>> ingestor = catalog.ingest.OpdsToCatalog(content)
>>> c = ingestor.getCatalog()

>>> #change atom+xml urls to b.a.o/view/IA/... scheme

>>> h = catalog.output.CatalogToHtml(c)
>>> html = h.toString()
>>> print html
"""
