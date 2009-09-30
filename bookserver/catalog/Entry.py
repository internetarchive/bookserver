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
>>> e = Entry.Entry({'urn'   :'urn:x-internet-archive:item:abuenosairesviaj00gonz',
...                  'url'   :'http://www.archive.org/download/abuenosairesviaj00gonz/abuenosairesviaj00gonz.pdf',
...                  'title' : 'abuenosairesviaj00gonz',
...                })

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
        'urn'                 : unicode,
        'url'                 : unicode,
        'title'               : unicode,
        'datestr'             : unicode,
        'content'             : unicode,
        'downloadsPerMonth'   : unicode,
        'updated'             : unicode,
        'identifier'          : unicode,
        'date'                : unicode,
        
        'publishers'          : list,
        'contributors'        : list,
        'languages'           : list,
        'subjects'            : list,
        'oai_updatedates'     : list,
        'authors'             : list,
    }
    
    required_keys = ('urn', 'url', 'title')
    
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
    def __init__(self, obj):

        
        if not type(obj) == dict:
            raise TypeError("bookserver.catalog.Entry takes a dict argument!")
        
        for key, val in obj.iteritems():
            self.validate(key, val)

        for req_key in Entry.required_keys:
            if not req_key in obj:
                raise KeyError("required key %s not supplied!" % (req_key))

        self._entry = copy.deepcopy(obj) 
                
        
    def get(self, key):
        if key in self._entry:
            return self._entry[key]
        else:
            return None

    def set(self, key, value):
        self.validate(key, value)
        self._entry[key] = value


if __name__ == '__main__':
    import doctest
    doctest.testmod()
