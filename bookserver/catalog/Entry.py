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
>>> e = Entry.Entry({'urn':'urn:x-internet-archive:item:abuenosairesviaj00gonz'})

#getters and setters

>>> e.get('urn')
'urn:x-internet-archive:item:abuenosairesviaj00gonz'
>>> e.set('publisher', 'Internet Archive')
>>> e.get('publisher')
'Internet Archive'

#error checking examples:

>>> e = Entry.Entry({'foo' : 'bar'})
Traceback (most recent call last):
    ...
KeyError: 'invalid key in bookserver.catalog.Entry'

>>> e = Entry.Entry({'urn':['urn:x-internet-archive:item:abuenosairesviaj00gonz']})
Traceback (most recent call last):
    ...
ValueError: invalid value in bookserver.catalog.Entry

>>> e.set('foo', 'bar')
Traceback (most recent call last):
    ...
KeyError: 'invalid key in bookserver.catalog.Entry'
"""

import copy

class Entry():

    """
    valid_keys can be str or list
    """

    valid_keys = {
        'publisher' : str,
        'urn'       : str,
        'url'       : str,
        'title'     : str,
        'datestr'   : str,
        'content'   : str,
    }
    
    required_keys = ('urn', 'url', 'title')
    
    def validate(self, key, value):
        if key not in Entry.valid_keys:
            raise KeyError("invalid key in bookserver.catalog.Entry")

        valtype = Entry.valid_keys[key]
        
        if not type(value) == valtype:
            raise ValueError("invalid value in bookserver.catalog.Entry")
    

    # Entry()
    #___________________________________________________________________________        
    def __init__(self, obj):

        
        if not type(obj) == dict:
            raise TypeError("bookserver.catalog.Entry takes a dict argument!")
        
        for key, val in obj.iteritems():
            if key not in Entry.valid_keys:
                raise KeyError("invalid key in bookserver.catalog.Entry")
            
            valtype = Entry.valid_keys[key]
            
            if not type(val) == valtype:
                raise ValueError("invalid value in bookserver.catalog.Entry")
                        
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
