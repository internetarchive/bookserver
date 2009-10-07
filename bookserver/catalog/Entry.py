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
        
        'publishers'          : list, # Publishers of the book, (usually just one listed, or none)
        'contributors'        : list, # IA-specific, includes libraries who contributed book
        'languages'           : list, # Languages, currently copied directly from IA metadata (MARC 21 code list 3 letter codes)
                                      # See http://www.loc.gov/marc/languages/language_code.html
        'subjects'            : list, # For IA, typically come from MARC records
        'oai_updatedates'     : list, # From Solr, list of dates when item was modified
        'authors'             : list, # List of authors
    }
        
    required_keys = ('urn', 'title')
    
    def validate(self, key, value):
        if key not in Entry.valid_keys:
            raise KeyError("invalid key in bookserver.catalog.Entry: %s" % (key))

        wantedType = Entry.valid_keys[key]
        
        gotType = type(value)
        if not gotType == wantedType:
            error = True
            if unicode == wantedType:
                #we can convert types to unicode if needed
                if str == gotType or int == gotType:
                    error = False
            
            if error:
                raise ValueError("invalid value in bookserver.catalog.Entry: %s=%s should have type %s, but got type %s" % (key, value, wantedType, gotType))
    

    # Entry()
    #___________________________________________________________________________        
    def __init__(self, obj, links=None):

        
        if not type(obj) == dict:
            raise TypeError("bookserver.catalog.Entry takes a dict argument!")
        
        for key, val in obj.iteritems():
            self.validate(key, val)

        for req_key in Entry.required_keys:
            if not req_key in obj:
                raise KeyError("required key %s not supplied!" % (req_key))

        if not links:
            raise KeyError("links not supplied!")

        self._entry = copy.deepcopy(obj)
        self._links = links
                

    # get()
    #___________________________________________________________________________        
    def get(self, key):
        if key in self._entry:
            return self._entry[key]
        else:
            if key in Entry.valid_keys:
                if list == Entry.valid_keys[key]:
                    return []
                else:
                    return None
            else:
                raise KeyError("requested key %s is not valid in Entry" % key)

    # set()
    #___________________________________________________________________________        
    def set(self, key, value):
        self.validate(key, value)
        self._entry[key] = value


if __name__ == '__main__':
    import doctest
    doctest.testmod()
