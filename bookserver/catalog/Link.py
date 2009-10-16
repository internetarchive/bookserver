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

class Link:
    valid_keys = ('url', 'type', 'rel', 'price', 'currencycode', 'formats')
    required_keys = ('url', 'type')
    
    acquisition ='http://opds-spec.org/acquisition'                 # Free acquisition
    buying = 'http://opds-spec.org/acquisition/buying'
    lending = 'http://opds-spec.org/acquisition/lending'
    subscription = 'http://opds-spec.org/acquisition/subscription'
    sample = 'http://opds-spec.org/acquisition/sample'
    
    opds = 'application/atom+xml;profile=opds'
    html = 'text/html'
    
    acquisition_types = (acquisition, buying, lending, subscription, sample)
    
    def validate(self, key, value):
        if key not in Link.valid_keys:
            raise KeyError("invalid key in bookserver.catalog.Link: %s" % (key))
        
    def __init__(self, **kwargs):
        for key,val in kwargs.iteritems():
            self.validate(key, val)
            
        for req_key in Link.required_keys:
            if not req_key in kwargs:
                raise KeyError("required key %s not supplied for Link!" % (req_key))
        
        if 'price' in kwargs:
            if not 'currencycode' in kwargs:
                kwargs['currencycode'] = 'USD'
                
        self._data = kwargs    

    def get(self, key):
        return self._data.get(key, None)

    def set(self, key, value):
        self.validate(key, value)
        self._data[key] = value
