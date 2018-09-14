#!/usr/bin/env python

#Copyright(c)2009 Internet Archive. Software license GPL version 3.

"""
This script is a proxy that formats solr queries as OPDS
"""

import sys

import cgi
import internetarchive as ia
import json
import requests
import string
import time
import urllib
import web

import catalog as catalog
import catalog.output as output
import device
from config import HOST, PORT, PROTOCOL, DEBUG

SERVICE_URL = '%s://%s' % (PROTOCOL, HOST)
if PORT not in [80, 443]:
    SERVICE_URL += ':%s' % PORT
ARCHIVE_DOMAIN = 'archive.org'

numRows = 50
ES_URL = 'http://%s/advancedsearch.php?fl=loans__status__status,loans__status__num_waitlist,loans__status__last_loan_date,contributor,creator,date,description,format,identifier,language,month,publicdate,publisher,subject,title&output=json' % ARCHIVE_DOMAIN

# You can customize pubInfo:
pubInfo = {
    'name'       : 'Internet Archive',
    'uri'        : 'https://%s' % ARCHIVE_DOMAIN,
    'opdsroot'   : SERVICE_URL,
    'mimetype'   : 'application/atom+xml;profile=opds-catalog;kind=acquisition',
    'urnroot'    : 'urn:x-internet-archive:bookserver',
    'es_base'    : ES_URL,
    'query_base' : 'mediatype:texts+AND+openlibrary_edition:(*)+AND+format:abbyy+AND+format:scandata+AND+format:pdf+AND+NOT+collection:opensource+AND+NOT+collection:rosettaproject'
}

urls = (
    '/group/([^/]*)(?:/([0-9]*))?', 'Group',
    '/(.*)/',                       'Redirect',
    '/alpha.(xml|html)',            'AlphaList',
    '/alpha/(.)(?:/(.*))?',         'Alpha',
    '/authentication_document',     'Authentication',
    '/downloads.(xml|html)',        'Downloads',
    '/inlibrary(?:/([0-9]*))?',     'InLibrary',
    '/new(?:/(.*))?(|.html)',       'Newest',
    '/opensearch.xml',              'OpenSearchDescription',
    '/opensearch(.*)',              'Opensearch',
    '/search(.*)',                  'Htmlsearch',
    '/crawlable(?:/(.*))?(|.html)', 'Crawlable',
    '/(|index.html)',               'Index',
    '/borrow/(.*)',                 'Borrow',
    '/simple/loans',                'Loans',
    '/simple(.*)',                  'Simple', # Acquisition only entrypoint for SimplyE
    '/(.*)',                        'IndexRedirect',
    )

application = web.application(urls, globals()).wsgifunc()

def getDateString():
    """IA is continuously scanning books. Since this OPDS file is constructed
    from search engine results, let's change the updated date every midnight
    """
    t  = time.gmtime()
    datestr = time.strftime('%Y-%m-%dT%H:%M:%SZ',
                (t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0))
    return datestr

def getEnv(key, default=None):
    env = web.ctx['environ']
    return env[key] if env.has_key(key) else default

def getDevice():
    userAgent = getEnv('HTTP_USER_AGENT')
    return bookserver.device.Detect.createFromUserAgent(userAgent) if userAgent else None

# IA Catalog. Mainly for navigation feeds like Index and AlphaList, but also the SimplyE acquistion feed
class IACatalog(catalog.Catalog):
    def __init__(self, **kwargs):
        catalog.Catalog.__init__(self, **kwargs)
        opensearch = catalog.OpenSearch('%s/opensearch.xml' % pubInfo['opdsroot'])
        self.addOpenSearch(opensearch)
        self.addAuthentication('%s/authentication_document' % pubInfo['opdsroot'])

class Index:
    def GET(self, url):
        mode = 'xml'
        if url and url.endswith('.html'):
            mode = 'html'

        datestr = getDateString()

        c = IACatalog(
            title='Internet Archive Catalog',
            urn=pubInfo['urnroot'],
            url=pubInfo['opdsroot'] + '/',
            datestr=datestr,
            author='Internet Archive',
            authorUri='https://%s' % ARCHIVE_DOMAIN,
            crawlableUrl=pubInfo['opdsroot'] + '/crawlable',
        )

        if 'html' == mode:
            links = {'alpha': 'alpha.html',
                     'downloads': 'downloads.html',
                     'new': 'new.html',
                     'inlibrary': 'inlibrary'
            }
            _type = 'text/html'
        else:
            links = {'alpha': 'alpha.xml',
                     'downloads': 'downloads.xml',
                     'new': 'new',
                     'inlibrary': 'inlibrary',
            }
            _type = 'application/atom+xml;profile=opds-catalog'

        l = catalog.Link(url=links['alpha'], type=_type)
        e = catalog.Entry({'title': 'Alphabetical By Title',
                           'urn': pubInfo['urnroot'] + ':titles:all',
                           'updated': datestr,
                           'content': 'Alphabetical list of all titles.'
                         }, links=(l,))
        c.addEntry(e)

        l = catalog.Link(url=links['downloads'], type=_type)
        e = catalog.Entry({'title': 'Most Downloaded Books',
                           'urn': pubInfo['urnroot'] + ':downloads',
                           'updated': datestr,
                           'content': 'The most downloaded books from the Internet Archive in the last month.'
                         }, links=(l,))
        c.addEntry(e)

        l = catalog.Link(url=links['new'], type=_type)
        e = catalog.Entry({'title': 'Recent Scans',
                           'urn': pubInfo['urnroot'] + ':new',
                           'updated': datestr,
                           'content': 'Books most recently scanned by the Internet Archive.'
                         }, links=(l,))
        c.addEntry(e)

        l = catalog.Link(url=links['inlibrary'], type=_type)
        e = catalog.Entry({'title': 'In Library',
                           'urn': pubInfo['urnroot'] + ':inlibrary',
                           'updated': datestr,
                           'content': 'Internet Archive core lending collection.'
                         }, links=(l,))
        c.addEntry(e)

        # Load navigation links for Groups
        for name, group in Group.groups.iteritems():
            l = catalog.Link(url='group/%s' % name, type=_type + ';kind=acquisition')
            e = catalog.Entry({'title': group['title'],
                               'urn': '%s:%s' % (pubInfo['urnroot'], name),
                               'updated': datestr,
                               # TODO: Add something more informative below
                               #'content': group['title']
                              }, links=(l,))
            c.addEntry(e)

        if url and url.endswith('.html'):
            r = output.ArchiveCatalogToHtml(c, device=getDevice())
            web.header('Content-Type', 'text/html')
            return r.toString()
        else:
            r = output.CatalogToAtom(c)
            web.header('Content-Type', 'application/atom+xml;profile=opds-catalog;kind=navigation')
            return r.toString()

# /group/{various groups formed by IA queries}/1
class Group:
    groups = {
        'recentreturns': {
            'title': 'Recently Returned',
            'q'    : 'collection:(inlibrary) AND loans__status__status:AVAILABLE&sort[]=loans__status__last_loan_date+desc'},
        'staffpicks': {
            'title': 'Books We Love',
            'q'    : '(collection:(inlibrary) OR (!collection:(printdisabled))) AND languageSorter:("English") AND openlibrary_subject:openlibrary_staff_picks&sort[]=loans__status__status'},
        'romance': {
            'title': 'Romance',
            'q'    : 'collection:(inlibrary) AND loans__status__status:AVAILABLE AND subject:(romance)'},
        'kids': {
            'title': 'Kids',
            'q'    : 'collection:(inlibrary) AND loans__status__status:AVAILABLE AND (creator:("parish, Peggy") OR creator:("avi") OR title:("goosebumps") OR creator:("Dahl, Roald") OR creator:("ahlberg, allan") OR creator:("Seuss, Dr") OR creator:("Carle, Eric") OR creator:("Pilkey, Dav")) AND !publisher:"Reinbek : Rowohlt"'},
        'thrillers': {
            'title': 'Thrillers',
            'q'    : '''collection:(inlibrary) AND loans__status__status:AVAILABLE AND (creator:"Clancy, Tom" OR creator:"King, Stephen" OR creator:"Clive Cussler" OR creator:("Cussler, Clive") OR creator:("Dean Koontz") OR creator:("Koontz, Dean") OR creator:("Higgins, Jack")) AND !publisher:"Pleasantville, N.Y. : Reader's Digest Association" AND languageSorter:"English"'''},
        'textbooks': {
             'title': 'Textbooks',
             'q'    : '(collection:(inlibrary) OR (!collection:(printdisabled))) AND loans__status__status:AVAILABLE AND openlibrary_subject:textbooks'},
        'partners': {
             'title': 'Authors Alliance & MIT Press',
             'q'    : '(collection:(inlibrary) OR (!collection:(printdisabled))) AND (openlibrary_subject:(authorsalliance) OR collection:(mitpress) OR publisher:(MIT Press) OR openlibrary_subject:(mitpress)) AND loans__status__status:AVAILABLE'},
        'openaudiobooks': {
             'title': 'Open Audiobooks',
                 'q': 'collection:librivoxaudio'},
    }

    def GET(self, name, page):
        if name not in self.groups:
            return web.seeother('/')
        group = self.groups[name]
        if not page:
            page = 1
        page = int(page)
        if page < 1:
            return web.seeother('/group/%s' % name)
        es_url   = '%s&q=%s&page=%d&rows=%d' % (pubInfo['es_base'], group['q'], page, numRows)
        urn      = '%s:group:%s' % (pubInfo['urnroot'], name)
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=numRows,
                                                urlBase='%s/group/%s/' % (pubInfo['opdsroot'], name),
                                                titleFragment=group['title'])
        c = ingestor.getCatalog()
        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(c, fabricateContentElement=True)
        return r.toString()

# /alpha/a/1
class Alpha:

    def GET(self, letter, page):
        mode = 'xml'
        if not page:
            page = 1
        else:
            if page.endswith('.html'):
                page = page[:-5]
                mode = 'html'
            page = int(page)

        es_url = (pubInfo['es_base'] + '&q=' + pubInfo['query_base'] +
                   '+AND+firstTitle%3A' + letter.upper() +
                   '&sort[]=titleSorter+asc&rows=' + str(numRows) +
                   '&page=' + str(page))
        titleFragment = 'books starting with "%s"' % (letter.upper())
        urn = '%s:%s:%d' % (pubInfo['urnroot'], letter, page)

        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=numRows,
                                                urlBase='%s/alpha/%s/' % (pubInfo['opdsroot'], letter),
                                                titleFragment=titleFragment)
        c = ingestor.getCatalog()

        if 'html' == mode:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            return r.toString()
        else:
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True)
            return r.toString()

# /alpha.xml
class AlphaList:
    def alphaURL(self, extension, letter, page):
        url = 'alpha/%s/%d' % (letter, page)
        if 'xml' != extension:
            url += '.' + extension
        return url

    def GET(self, extension):
        #IA is continuously scanning books. Since this OPDS file is constructed
        #from search engine results, let's change the updated date every midnight
        #TODO: create a version of /alpha.xml with the correct updated dates,
        #and cache it for an hour to ease load on solr
        datestr = getDateString()

        c = IACatalog(title     = 'Internet Archive - All Titles',
                      urn       = pubInfo['urnroot'] + ':titles:all',
                      url       = pubInfo['opdsroot'] + '/alpha.xml',
                      datestr   = datestr,
                      author    = 'Internet Archive',
                      authorUri = 'https://%s' % ARCHIVE_DOMAIN,
                      crawlableUrl = pubInfo['opdsroot'] + '/crawlable')

        for letter in string.ascii_uppercase:
            lower = letter.lower()

            if 'html' == extension:
                linkType = 'text/html'
            elif 'xml' == extension:
                linkType = 'application/atom+xml'
            else:
                raise ValueError('Unsupported extension %s' % extension)

            l = catalog.Link(url = self.alphaURL(extension, lower, 1), type = linkType)
            e = catalog.Entry({'title'   : 'Titles: ' + letter,
                               'urn'     : pubInfo['urnroot'] + ':titles:' + lower,
                               'updated' : datestr,
                               'content' : 'Titles starting with ' + letter
                             }, links=(l,))
            c.addEntry(e)

        if ('xml' == extension):
            web.header('Content-Type', 'application/atom+xml;profile=opds-catalog;kind=navigation')
            r = output.CatalogToAtom(c)
            return r.toString()
        else:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            return r.toString()

# /downloads.xml
class Downloads:
    def GET(self, extension):
        es_url = (pubInfo['es_base'] + '&q=' + pubInfo['query_base'] + '&sort[]=month+desc&rows=' + str(numRows))
        titleFragment = 'Most Downloaded Books in the last Month'
        urn = pubInfo['urnroot'] + ':downloads'
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn, titleFragment=titleFragment,
                                                  urlBase='%s/downloads.xml' % pubInfo['opdsroot'])
        c = ingestor.getCatalog()

        if ('xml' == extension):
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True)
            return r.toString()
        elif ('html' == extension):
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            return r.toString()
        else:
            web.seeother('/')

# /new/1
class Newest:
    def GET(self, page, extension):
        if extension == '.html':
            extension = 'html'
        else:
            extension = 'xml'

        if not page:
            page = 1
        else:
            if page.endswith('.html'):
                extension = 'html'
                page = page[:-5]
            page = int(page)

        es_url   = pubInfo['es_base'] + '&q=' + pubInfo['query_base'] + '&sort[]=publicdate+desc&rows=' + str(numRows) + '&page=' + str(page)
        titleFragment = 'books sorted by update date'
        urn      = pubInfo['urnroot'] + ':new:%d' % (page)
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=numRows,
                                                urlBase='%s/new/' % pubInfo['opdsroot'],
                                                titleFragment=titleFragment)
        c = ingestor.getCatalog()
        if 'html' == extension:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device=getDevice())
            return r.toString()
        else:
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True)
            return r.toString()


# Acquisition feed grouped by 'collection' for SimplyE
class Simple:
    def GET(self, extension):
        urn = '%s:simple' % (pubInfo['urnroot'])
        url = '%s/simple/' % (pubInfo['opdsroot'])

        # base catalog to append collection entries to
        main = IACatalog(title='Internet Archive OPDS Simple Feed', urn=urn, url=url)

        # iterate over Groups, and add rel=collection for each
        for name, group in Group.groups.iteritems():
            rows     = 15
            es_url   = '%s&q=%s&rows=%d' % (pubInfo['es_base'], group['q'], rows)
            urn      = '%s:group:%s' % (pubInfo['urnroot'], name)
            urlBase  = '%s/group/%s/' % (pubInfo['opdsroot'], name)
            ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                      page=1, numRows=rows,
                                                      urlBase=urlBase,
                                                      titleFragment=group['title'])
            c = ingestor.getCatalog()
            # url below does not work if relative
            l = catalog.Link(url=urlBase, type='application/atom+xml;profile=opds-catalog;kind=acquisition', rel='collection', title=group['title'])
            for entry in c.getEntries():
                entry._links = entry._links + (l,)
                # TODO: this should really look for the latest datestr, but currently they are all identical
                main._datestr = c._datestr
                main.addEntry(entry)

        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(main, fabricateContentElement=True)
        return r.toString()


class Borrow:
    def GET(self, ocaid):
        webdata = web.ctx.env
        auth = webdata.get('HTTP_AUTHORIZATION')

        if not auth:
            raise Loans.Unauthorized()
        else:
            email, password = auth[6:].decode('base64').split(':')
            # Use basic auth credentials to retrive archive.org s3 keys
            try:
                s3keys = ia.config.get_auth_config(email, password)
            except ia.exceptions.AuthenticationError:
                raise Loans.Unauthorized()

            # POST to archive.org with s3 keys to get acsm url
            loans_url = "https://%s/services/loans/beta/loan/?action=media_url&identifier=%s&format=epub" % (ARCHIVE_DOMAIN, ocaid)
            r = requests.post(loans_url, data=s3keys.get('s3', {}))
            if r.status_code != 200:
                web.header('Content-Type', 'application/api-problem+json')
                details = {'status': 404,
                           'type': 'http://librarysimplified.org/terms/problem/no-licenses',
                           'detail': 'The item you requested (%s) is not in this collection.' % ocaid,
                           'title': 'No licenses.'}
                raise web.NotFound(json.dumps(details))

            # On success show single entry OPDS feed, with link to the acsm file
            acsm_url = r.json().get('url')
            entry = """<entry>
                    <link href="%s" rel="http://opds-spec.org/acquisition" type="application/vnd.adobe.adept+xml">
                    <opds:indirectAcquisition type="application/epub+zip"/>
                    </link></entry>""" % acsm_url
            web.header('Content-Type', 'application/atom+xml;type=entry;profile=opds-catalog')
            web.ctx.status = '201 Created'
            return entry

class Loans:
    class Unauthorized(web.HTTPError):
        headers = {
            'Content-Type': 'application/vnd.opds.authentication.v1.0+json',
            'Link'        : '<%s/authentication_document>; rel=http://opds-spec.org/auth/document; type="application/vnd.opds.authentication.v1.0+json"' % pubInfo['opdsroot'],
            'WWW-Authenticate': 'Basic realm="Library card"',
        }

        def __init__(self):
            return web.HTTPError.__init__(self, '401 Unauthorized', headers=self.headers, data=Authentication.DOCUMENT)

    def GET(self):
        webdata = web.ctx.env
        auth = webdata.get('HTTP_AUTHORIZATION')
        raise self.Unauthorized()


class InLibrary:
    def GET(self, page):
        if not page:
            page = 1
        page = int(page)
        es_url = pubInfo['es_base'] + '&q=' + pubInfo['query_base'] + '+AND+collection:inlibrary&rows=' + str(numRows) + '&page=' + str(page)
        titleFragment = 'books in library'
        urn = pubInfo['urnroot'] + ':inlibrary:%d' % (page)
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=numRows,
                                                urlBase='%s/inlibrary/' % pubInfo['opdsroot'],
                                                titleFragment=titleFragment)
        c = ingestor.getCatalog()

        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(c, fabricateContentElement=True)
        return r.toString()

# /crawlable/1
class Crawlable:
    def GET(self, page, extension):
        if extension == '.html':
            extension = 'html'
        else:
            extension = 'xml'

        if not page:
            page = 1
        else:
            if page.endswith('.html'):
                extension = 'html'
                page = page[:-5]
            page = int(page)

        crawlNumRows = 1000;
        es_url  = pubInfo['es_base'] + '&q=' + pubInfo['query_base'] + '&rows=' + str(crawlNumRows) + '&page=' + str(page)
        titleFragment = '- crawlable feed'
        urn      = pubInfo['urnroot'] + ':crawl:%d' % (page)
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=crawlNumRows,
                                                urlBase='%s/crawlable/' % pubInfo['opdsroot'],
                                                titleFragment=titleFragment)
        c = ingestor.getCatalog()

        if 'html' == extension:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device=getDevice())
            return r.toString()
        else:
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True)
            return r.toString()


# /opensearch
class Opensearch:
    def GET(self, query):
        params = cgi.parse_qs(web.ctx.query)

        if not 'page' in params:
            page = 1
        else:
            page = int(params['page'][0])

        q = params['?q'][0]
        qq = urllib.quote(q)
        es_url = pubInfo['es_base'] + '&q=' + qq + '+AND+' + pubInfo['query_base'] + '&sort[]=month+desc&rows=' + str(numRows) + '&page=' + str(page)
        titleFragment = 'search results for ' + q
        urn    = pubInfo['urnroot'] + ':search:%s:%d' % (qq, page)

        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=numRows,
                                                urlBase='%s/opensearch?q=%s&page=' % (pubInfo['opdsroot'], qq),
                                                titleFragment=titleFragment)
        c = ingestor.getCatalog()

        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(c, fabricateContentElement=True)
        return r.toString()

# /search
class Htmlsearch:
    def GET(self, query):
        qs = web.ctx.query
        if qs.startswith('?'):
            qs = qs[1:]

        params = cgi.parse_qs(qs)

        if not 'page' in params:
            page = 1
        else:
            page = params['page'][0] # XXX hack for .html ending -- remove once fixed
            if page.endswith('.html'):
                page = page[:-5]
            page = int(page)

        q = params['q'][0]
        qq = urllib.quote(q)
        # NOTE: xxx this is wrong -- SOLR is dead -- have reported and hasnt been corrected yet --tracey jul2017
        es_url = 'http://se.us.archive.org:8983/solr/select?q='+qq+'+AND+'+pubInfo['query_base']+'&fl=identifier,title,creator,oai_updatedate,date,contributor,publisher,subject,language,format&rows='+str(numRows)+'&page='+str(page)+'&wt=json'
        titleFragment = 'search results for ' + q
        urn = pubInfo['urnroot'] + ':search:%s:%d' % (qq, page)

        ingestor = catalog.ingest.SolrToCatalog(pubInfo, es_url, urn,
                                                page=page, numRows=numRows,
                                                urlBase='%s/search?q=%s&page=' % (pubInfo['opdsroot'], qq), # XXX adding .html to end...
                                                titleFragment=titleFragment)
        c = ingestor.getCatalog()

        web.header('Content-Type', 'text/html')
        r = output.ArchiveCatalogToHtml(c, device = getDevice())
        return r.toString()


# /authentication_document - Authentication Document
class Authentication:
    DOCUMENT = """{
    "title": "Internet Archive",
    "id": "%s/authentication_document",
    "color_scheme": "black",
    "description": "archive.org Login",
    "service_area": "everywhere",
    "service_description": "Universal Access to All Knowledge",
    "authentication": [
        {
            "type": "http://opds-spec.org/auth/basic",
            "inputs": {
                "login": {
                    "keyboard": "Email address"
                },
                "password": {
                    "keyboard": "Default"
                }
            },
            "labels": {
                "login": "Email address",
                "password": "Password"
            }
        }
     ],
     "links": [
         {"rel": "about", "href": "https://archive.org/about/", "type": "text/html"},
         {"rel": "alternate", "href": "https://archive.org", "type": "text/html"},
         {"rel": "help", "href": "mailto:info@archive.org"},
         {"rel": "logo", "href": "https://archive.org/logos/hires/ia-tight-480x480.jpg", "type": "image/jpeg"},
         {"rel": "privacy-policy", "href": "https://archive.org/about/terms.php", "type": "text/html"},
         {"rel": "register", "href": "https://archive.org/account/login.createaccount.php", "type": "text/html"},
         {"rel": "start", "href": "https://bookserver.archive.org/catalog/simple", "type": "application/atom+xml;profile=opds-catalog;kind=acquisition"},
         {"rel": "support", "href": "mailto:info@archive.org"},
         {"rel": "http://librarysimplified.org/rel/designated-agent/copyright", "href": "mailto:info@archive.org"}
     ]
}""" % pubInfo['opdsroot']

    def GET(self):
        web.header('Content-Type', 'application/vnd.opds.authentication.v1.0+json')
        return self.DOCUMENT


# /opensearch.xml - Open Search Description
class OpenSearchDescription:
    def GET(self):
        web.header('Content-Type', 'application/atom+xml')
        return """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Internet Archive Search</ShortName>
    <Description>Search archive.org's OPDS Catalog.</Description>
    <Url type="application/atom+xml;profile=opds-catalog;kind=acquisition" template="%s/opensearch?q={searchTerms}"/>
</OpenSearchDescription>""" % (pubInfo['opdsroot'])


# redirect to remove trailing slash
class Redirect:
    def GET(self, path):
        web.seeother('/' + path)


# redirect to index
class IndexRedirect:
    def GET(self, path):
        web.seeother('/')


# main() - standalone mode
if __name__ == "__main__":
    class OPDServer(web.application):
        def run(self, host='0.0.0.0', port='8080', *middleware):
            func = self.wsgifunc(*middleware)
            return web.httpserver.runsimple(func, (host, port))
    app = OPDServer(urls, globals())
    app.run(port=PORT)
