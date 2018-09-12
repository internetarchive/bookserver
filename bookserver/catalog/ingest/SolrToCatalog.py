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

import urllib
import time
import datetime

import sys
sys.path.append("/petabox/sw/lib/python")
import simplejson as json

from .. import Catalog
from ..Entry import IAEntry, Entry
from .. import Navigation
from .. import OpenSearch
from .. import Link
import catalog.language

class SolrToCatalog:

    # map of solr field names to catalog key names
    # catalog key names that are plural are lists instead of strings
    keymap = {
              'identifier'     : 'identifier',
              'title'          : 'title',
              'date'           : 'date',
              'month'          : 'downloadsPerMonth',
              'price'          : 'price',
              'currencyCode'   : 'currencyCode',
              'provider'       : 'provider',
              'urn'            : 'urn',
              'summary'        : 'summary',
              'description'    : 'description',
              'updated'        : 'updated',
              'publicdate'     : 'publicdate',
              'publisher'      : 'publisher',

              #these are lists, not strings
              'creator'        : 'authors',
              'subject'        : 'subjects',
              'language'       : 'languages',
              'contributor'    : 'contributors',
              'link'           : 'links',
              'rights'         : 'rights',

              'oai_updatedate' : 'oai_updatedates',
              'format'         : 'formats',

             }

    # removeKeys()
    #___________________________________________________________________________
    def removeKeys(self, d, keys):
        for key in keys:
            d.pop(key, None)


    # entryFromSolrResult()
    #___________________________________________________________________________
    def entryFromSolrResult(self, item, pubInfo):
        #use generator expression to map dictionary key names
        bookDict = dict( (SolrToCatalog.keymap[key], val) for key, val in item.iteritems() )

        links = []
        if 'price' in bookDict:
            if 0.0 == bookDict['price']:
                rel = 'http://opds-spec.org/acquisition'
                price = '0.00'
            else:
                price = str(bookDict['price'])
                rel = 'http://opds-spec.org/acquisition/buying'
        else:
            price = '0.00'
            rel = 'http://opds-spec.org/acquisition'

        if 'currencyCode' in bookDict:
            currencycode = bookDict['currencyCode']
        else:
            currencycode = 'USD'

        if not 'updated' in bookDict:
            #how did this happen?
            bookDict['updated'] = self.getDateString()

        for link in bookDict['links']:
            if link.endswith('.pdf'):
                l = Link(url  = link, type = 'application/pdf',
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)
            elif link.endswith('.epub'):
                l = Link(url  = link, type = 'application/epub+zip',
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)
            elif link.endswith('.mobi'):
                l = Link(url  = link, type = 'application/x-mobipocket-ebook',
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)
            else:
                l = Link(url  = link, type = 'text/html',
                               rel = rel,
                               price = price,
                               currencycode = currencycode)
                links.append(l)

        if 'rights' in bookDict:
            rightsStr = ''
            for right in bookDict['rights']:
                #special case for Feedbooks
                if not '' == right:
                    rightsStr += right + ' '
            if '' == rightsStr:
                self.removeKeys(bookDict, ('rights',))
            else:
                bookDict['rights'] = rightsStr

        self.removeKeys(bookDict, ('links','price', 'currencyCode'))
        e = Entry(bookDict, links=links)

        return e

    # SolrToCatalog()
    #___________________________________________________________________________
    def __init__(self, pubInfo, url, urn, page=None, numRows=None, urlBase=None, titleFragment=None):

        self.url = url
        f = urllib.urlopen(self.url)
        contents = f.read()
        f.close()
        try:
            obj = json.loads(contents)
        except ValueError:
            # No search results - fake response object
            obj = { 'response': {
                'docs': [],
                'numFound': 0,
            }}

        numFound = int(obj['response']['numFound'])

        title = pubInfo['name'] + ' Catalog'

        if titleFragment is not None:
            title = titleFragment

        # TODO: Pagination counts are not displaying nicely on clients with infinite scroll
        #   - rethink and reimplement if still required
        #if page is not None:
        #    if 0 == numFound:
        #        title += ' - no results'
        #    else:
        #        title += ' - '
        #        if numRows > 0:
        #            title += '%d to %d of ' % ((page-1)*numRows + 1, min(page*numRows, numFound))
        #        title += "%d" % (numFound)

        self.c = Catalog(title     = title,
                         urn       = urn,
                         url       = urlBase,
                         author    = pubInfo['name'],
                         authorUri = pubInfo['uri'],
                         datestr   = self.getDateString(),
                        )

        nav = Navigation.initWithBaseUrl(page, numRows, numFound, urlBase)
        self.c.addNavigation(nav)

        opensearch = OpenSearch('%s/opensearch.xml' % pubInfo['opdsroot'])
        self.c.addOpenSearch(opensearch)
        self.c.addAuthentication('%s/authentication_document' % pubInfo['opdsroot'])

        for item in obj['response']['docs']:
            entry = self.entryFromSolrResult(item, pubInfo)
            self.c.addEntry(entry)

    # getCatalog()
    #___________________________________________________________________________
    def getCatalog(self):
        return self.c

    # getDateString()
    #___________________________________________________________________________
    def getDateString(self):
        #IA is continuously scanning books. Since this OPDS file is constructed
        #from search engine results, let's change the updated date every midnight
        t       = time.gmtime()
        datestr = time.strftime('%Y-%m-%dT%H:%M:%SZ',
                    (t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0))
        return datestr

    def nextPage(self):
        raise NotImplementedError

    def prevPage(self):
        raise NotImplementedError


# IASolrToCatalog()
#_______________________________________________________________________________
# The solr used for archive.org has a slightly different schema than the one
# recommended for a bookserver installation.

class IASolrToCatalog(SolrToCatalog):
    def entryFromSolrResult(self, item, pubInfo):
        #use generator expression to map dictionary key names
        bookDict = dict( (SolrToCatalog.keymap.get(key), val) for key, val in item.iteritems() if SolrToCatalog.keymap.get(key) )
        if 'publicdate' in item:
            bookDict['updated'] = item['publicdate']
        else:
            bookDict['updated'] = self.getDateString()

        self.removeKeys(bookDict, ('publicdate',))

        #IA scribe books use MARC language codes
        if item.get('language'):
            languages = set(item['language']) if isinstance(item['language'], list) else set([item['language']])
            bookDict['languages'] = [catalog.language.iso_639_23_to_iso_639_1(language) for language in languages]

        # Is the book borrowable?
        if 'loans__status__status' in item:
            acquisition_type = 'borrow'
            avail = item.get('loans__status__status')
            if avail == 'AVAILABLE':
                copies = '1'
            else:
                copies = '0'
            holds = item.get('loans__status__num_waitlist')
            availability = {'availability': avail.lower(), 'holds': holds, 'copies': copies, 'date': self.availableDate(item)}
        else:
            acquisition_type = 'open-access'
            availability = {}

        bookDict['urn'] = pubInfo['urnroot'] + ':item:' + item['identifier']

        webLink = Link(url='https://archive.org/details/%s' % item['identifier'],
                       type='text/html',
                       rel='http://opds-spec.org/acquisition/%s' % acquisition_type,
                       **availability)

        borrowLink = Link(url='%s/borrow/%s' % (pubInfo['opdsroot'], item['identifier']),
                          type='application/atom+xml;type=entry;profile=opds-catalog',
                          rel='http://opds-spec.org/acquisition/%s' % acquisition_type,
                          **availability)

        pdfLink = Link(url='https://archive.org/download/%s/%s.pdf' % (item['identifier'], item['identifier']),
                       type='application/pdf',
                       rel='http://opds-spec.org/acquisition/%s' % acquisition_type,
                       **availability)

        epubLink = Link(url='https://archive.org/download/%s/%s.epub' % (item['identifier'], item['identifier']),
                        type='application/epub+zip',
                        rel='http://opds-spec.org/acquisition/%s' % acquisition_type,
                        **availability)

        coverLink = Link(url='http://archive.org/download/%s/page/cover_medium.jpg' % (item['identifier']),
                         type='image/jpeg', rel='http://opds-spec.org/image')

        thumbLink = Link(url='http://archive.org/download/%s/page/cover_thumb.jpg' % (item['identifier']),
                         type='image/jpeg', rel='http://opds-spec.org/image/thumbnail')

        audiobook = 'LibriVox Apple Audiobook' in item.get('format')

        if audiobook:
            thumb_url = 'https://archive.org/services/img/%s' % item['identifier']
            coverLink = Link(url=thumb_url, type='image/jpeg', rel='http://opds-spec.org/image')
            thumbLink = Link(url=thumb_url, type='image/jpeg', rel='http://opds-spec.org/image/thumbnail')
            audiobookLink = Link(url='https://api.archivelab.org/books/%s/opds_audio_manifest' % item['identifier'],
                                 type='application/audiobook+json',
                                 rel='http://opds-spec.org/acquisition/%s' % acquisition_type)
            webLink = Link(url='https://archive.org/details/%s' % item['identifier'],
                           type='text/html',
                           rel='http://opds-spec.org/acquisition/%s' % acquisition_type)

        if acquisition_type == 'borrow':
            links = (webLink, borrowLink, coverLink, thumbLink)
        elif audiobook:
            links = (audiobookLink, webLink, coverLink, thumbLink)
        else:
            links = (pdfLink, epubLink, coverLink, thumbLink)

        e = IAEntry(bookDict, links=links)

        return e

    def availableDate(self, item):
        borrowed = item.get('loans__status__last_loan_date')
        if borrowed is None:
            return
        loan_period = 14
        waiting = int(item.get('loans__status__num_waitlist', 0))
        date = datetime.datetime.strptime(borrowed, '%Y-%m-%dT%H:%M:%SZ') + datetime.timedelta(days=(1+waiting)*loan_period)
        return date.strftime('%Y-%m-%d')
