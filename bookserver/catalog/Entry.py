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

>>> import Entry
>>> import Link
>>> l = Link.Link(url  = 'http://www.archive.org/download/abuenosairesviaj00gonz/abuenosairesviaj00gonz.pdf',
...               type = 'application/pdf', rel='http://opds-spec.org/acquisition')
>>> e = Entry.Entry({'urn'   :'urn:x-internet-archive:item:abuenosairesviaj00gonz',
...                  'title' : 'abuenosairesviaj00gonz'}, links = [l])

#getters and setters

>>> e.get('urn')
'urn:x-internet-archive:item:abuenosairesviaj00gonz'
>>> e.set('publishers', ['Internet Archive'])
>>> e.get('publishers')
['Internet Archive']

#error checking examples:

>>> e = Entry.Entry({'foo' : 'bar'})
Traceback (most recent call last):
    ...
KeyError: 'invalid key in bookserver.catalog.Entry: foo'

>>> e = Entry.Entry({'urn':['urn:x-internet-archive:item:abuenosairesviaj00gonz']})
Traceback (most recent call last):
    ...
ValueError: invalid value in bookserver.catalog.Entry: urn=['urn:x-internet-archive:item:abuenosairesviaj00gonz'] should have type <type 'unicode'>, but got type <type 'list'>

>>> e.get('languages')
[]

>>> e.get('date') #unset scalar returns None

>>> e.get('foo')
Traceback (most recent call last):
    ...
KeyError: 'requested key foo is not valid in Entry'

>>> e.set('foo', 'bar')
Traceback (most recent call last):
    ...
KeyError: 'invalid key in bookserver.catalog.Entry: foo'
"""

import copy

class Entry():

    """
    valid_keys can be str or list
    TODO: These key names come from the IA solr keys.
          We should rename them to be similar to feedparser keys
          i.e. dcterms_language instead of languages
    """

    valid_keys = {
        'urn'                 : unicode, # Site-specific identifier, used to uniquely identify Atom entry
        'url'                 : unicode, # Acquisition links, there may be multiple with different types - soon to be list of multiple links, with different types
        'title'               : unicode, # Item title
        'content'             : unicode, # Free-form text or HTML that describes the item
        'downloadsPerMonth'   : unicode, # IA-specific, downloads of item in last 30 days
        'updated'             : unicode, # The last time information about this entry (not the book content) was updated
        'identifier'          : unicode, # Archive item ID
        'date'                : unicode, # Publication date
        'rights'              : unicode, # atom:rights
        'summary'             : unicode, # atom:summary
        'dcterms_source'      : unicode, # dcterms:source
        'provider'            : unicode,
        'publisher'           : unicode, # Publishers of the book, dcterm:publisher is occurrence [0..1], http://www.datypic.com/sc/dc/e-dcterms_publisher.html

        'description'         : list, # IA items can have multiple descriptions
        'contributors'        : list, # IA-specific, includes libraries who contributed book
        'languages'           : list, # Languages, currently copied directly from IA metadata (MARC 21 code list 3 letter codes)
                                      # See http://www.loc.gov/marc/languages/language_code.html
        'subjects'            : list, # For IA, typically come from MARC records
        'oai_updatedates'     : list, # From Solr, list of dates when item was modified
        'authors'             : list, # List of authors
        'formats'             : list,
    }

    required_keys = ('urn', 'title')

    def validate(self, key, value):
        if key not in self.valid_keys:
            raise KeyError("invalid key in bookserver.catalog.Entry: %s" % (key))

        wantedType = self.valid_keys[key]
        gotType = type(value)
        if not gotType == wantedType:
            error = True
            if wantedType is list:
                self._entry[key] = [value]
                error = False
            if wantedType is unicode:
                #we can convert types to unicode if needed
                if str is gotType or int is gotType:
                    error = False
                if gotType == list:
                    # If more than one expected value, e.g. title in other language, japaneseforevery00susu
                    #  pick the first to avoid errors
                    self._entry[key] = value[0]
                    error = False

            if error:
                raise ValueError("invalid value in bookserver.catalog.Entry: %s=%s should have type %s, but got type %s for item %s" % (key, value, wantedType, gotType, self.get('identifier')))


    def __init__(self, obj, links=None):
        if not type(obj) == dict:
            raise TypeError("bookserver.catalog.Entry takes a dict argument!")

        if 'title' not in obj:
            obj['title'] = '(no title)' #special case for IA test items

        for req_key in Entry.required_keys:
            if not req_key in obj:
                raise KeyError("required key %s not supplied!" % (req_key))

        if not links:
            raise KeyError("links not supplied!")

        self._entry = copy.deepcopy(obj)
        self._links = links
        for key, val in obj.iteritems():
            self.validate(key, val)


    def get(self, key):
        if key in self._entry:
            return self._entry[key]
        else:
            if key in self.valid_keys:
                if list == self.valid_keys[key]:
                    return []
                else:
                    return None
            else:
                raise KeyError("requested key %s is not valid in Entry" % key)

    def set(self, key, value):
        self.validate(key, value)
        self._entry[key] = value


    def getLinks(self):
        return self._links


class IAEntry(Entry):
    """
    Catalog entry with extra keys specific to the Internet Archive.
    """
    # Add our IA-specific "formats" key
    valid_keys = Entry.valid_keys.copy()
    valid_keys['formats'] = list

if __name__ == '__main__':
    import doctest
    doctest.testmod()
