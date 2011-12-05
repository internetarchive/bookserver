#!/usr/bin/env python

#Copyright(c)2009 Internet Archive. Software license GPL version 3.

"""
This script is a proxy that formats solr queries as OPDS
"""

import sys
sys.path.append("/petabox/sw/lib/python")

import web
import time
import string
import cgi
import urllib

import bookserver.catalog as catalog
import bookserver.catalog.output as output
import bookserver.device

numRows = 50

# You can customize pubInfo:
pubInfo = {
    'name'       : 'Internet Archive',
    'uri'        : 'http://www.archive.org',
    'opdsroot'   : 'http://bookserver.archive.org/catalog',
    'mimetype'   : 'application/atom+xml;profile=opds',
    'url_base'   : '/catalog',
    'urnroot'    : 'urn:x-internet-archive:bookserver:catalog',
    'solr_base'  : 'http://se.us.archive.org:8983/solr/select?fl=identifier,title,creator,publicdate,date,contributor,publisher,subject,language,format,month&wt=json',
    'query_base' : 'format%3Aabbyy+AND+format%3Ascandata+AND+format%3Apdf+AND+NOT+ocr%3A%22language+not%22+AND+NOT+collection%3Alendinglibrary+AND+NOT+collection%3Aopensource+AND+NOT+collection%3Aprintdisabled+AND+NOT+collection%3Arosettaproject'
}

urls = (
    '/(.*)/',                       'redirect',
    '/alpha.(xml|html)',            'alphaList',
    '/alpha/(.)(?:/(.*))?',         'alpha',
    '/downloads.(xml|html)',        'downloads',
    '/new(?:/(.*))?(|.html)',       'newest',
    '/opensearch.xml',              'openSearchDescription',
    '/opensearch(.*)',              'opensearch',
    '/search(.*)',                  'htmlsearch',
    '/crawlable(?:/(.*))?(|.html)', 'crawlable',
    '/(|index.html)',               'index',
    '/(.*)',                        'indexRedirect',
    )

application = web.application(urls, globals()).wsgifunc()



# getDateString()
#______________________________________________________________________________
def getDateString():
    #IA is continuously scanning books. Since this OPDS file is constructed
    #from search engine results, let's change the updated date every midnight
    t       = time.gmtime()
    datestr = time.strftime('%Y-%m-%dT%H:%M:%SZ',
                (t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0))
    return datestr

def getEnv(key, default = None):
    env = web.ctx['environ']
    if env.has_key(key):
        return env[key]
    else:
        return default

def getDevice():
    userAgent = getEnv('HTTP_USER_AGENT')
    if userAgent is not None:
        device = bookserver.device.Detect.createFromUserAgent(userAgent)
    else:
        device = None
    return device

# /
#______________________________________________________________________________
class index:
    def GET(self, url):
        mode = 'xml'
        if url and url.endswith('.html'):
            mode = 'html'

        datestr = getDateString()

        c = catalog.Catalog(
                            title     = 'Internet Archive Catalog',
                            urn       = pubInfo['urnroot'],
                            url       = pubInfo['opdsroot'] + '/',
                            datestr   = datestr,
                            author    = 'Internet Archive',
                            authorUri = 'http://www.archive.org',
                            crawlableUrl = pubInfo['opdsroot'] + '/crawlable',
                           )

        if 'html' == mode:
            links = { 'alpha': 'alpha.html',
                      'downloads': 'downloads.html',
                      'new': 'new.html'
            }
            type = 'text/html'
        else:
            links = {'alpha': 'alpha.xml',
                     'downloads': 'downloads.xml',
                     'new': 'new'
            }
            type = 'application/atom+xml'

        l = catalog.Link(url = links['alpha'], type = type)
        e = catalog.Entry({'title'  : 'Alphabetical By Title',
                           'urn'     : pubInfo['urnroot'] + ':titles:all',
                           'updated' : datestr,
                           'content' : 'Alphabetical list of all titles.'
                         }, links=(l,))
        c.addEntry(e)

        l = catalog.Link(url = links['downloads'], type = type)
        e = catalog.Entry({'title'   : 'Most Downloaded Books',
                           'urn'     : pubInfo['urnroot'] + ':downloads',
                           'updated' : datestr,
                           'content' : 'The most downloaded books from the Internet Archive in the last month.'
                         }, links=(l,))

        c.addEntry(e)

        l = catalog.Link(url = links['new'], type = type)
        e = catalog.Entry({'title'   : 'Recent Scans',
                           'urn'     : pubInfo['urnroot'] + ':new',
                           'updated' : datestr,
                           'content' : 'Books most recently scanned by the Internet Archive.'
                         }, links=(l,))

        c.addEntry(e)

        osDescriptionDoc = 'http://bookserver.archive.org/catalog/opensearch.xml'
        o = catalog.OpenSearch(osDescriptionDoc)
        c.addOpenSearch(o)

        if url and url.endswith('.html'):
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            web.header('Content-Type', 'text/html')
            return r.toString()
        else:
            r = output.CatalogToAtom(c)
            web.header('Content-Type', pubInfo['mimetype'])
            return r.toString()


# /alpha/a/0
#______________________________________________________________________________
class alpha:

    def GET(self, letter, start):
        mode = 'xml'
        if not start:
            start = 0
        else:
            if start.endswith('.html'):
                start = start[:-5]
                mode = 'html'
            start = int(start)

        solrUrl       = pubInfo['solr_base']+'&q='+pubInfo['query_base']+'+AND+firstTitle%3A'+letter.upper()+'&sort=titleSorter+asc&rows='+str(numRows)+'&start='+str(start*numRows)
        titleFragment = 'books starting with "%s"' % (letter.upper())
        urn           = pubInfo['urnroot'] + ':%s:%d'%(letter, start)

        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='/catalog/alpha/%s/' % (letter),
                                                titleFragment = titleFragment)
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
#______________________________________________________________________________
class alphaList:
    def alphaURL(self, extension, letter, start):
        url = 'alpha/%s/%d' % (letter, start)
        if 'xml' != extension:
            url += '.' + extension
        return url

    def GET(self, extension):
        #IA is continuously scanning books. Since this OPDS file is constructed
        #from search engine results, let's change the updated date every midnight
        #TODO: create a version of /alpha.xml with the correct updated dates,
        #and cache it for an hour to ease load on solr
        datestr = getDateString()

        c = catalog.Catalog(
                            title     = 'Internet Archive - All Titles',
                            urn       = pubInfo['urnroot'] + ':titles:all',
                            url       = pubInfo['opdsroot'] + '/alpha.xml',
                            datestr   = datestr,
                            author    = 'Internet Archive',
                            authorUri = 'http://www.archive.org',
                            crawlableUrl = pubInfo['opdsroot'] + '/crawlable',
                           )

        for letter in string.ascii_uppercase:
            lower = letter.lower()

            if 'html' == extension:
                linkType = 'text/html'
            elif 'xml' == extension:
                linkType = 'application/atom+xml'
            else:
                raise ValueError('Unsupported extension %s' % extension)

            l = catalog.Link(url = self.alphaURL(extension, lower, 0), type = linkType)
            e = catalog.Entry({'title'   : 'Titles: ' + letter,
                               'urn'     : pubInfo['urnroot'] + ':titles:'+lower,
                               'updated' : datestr,
                               'content' : 'Titles starting with ' + letter
                             }, links=(l,))
            c.addEntry(e)

        osDescriptionDoc = 'http://bookserver.archive.org/catalog/opensearch.xml'
        o = catalog.OpenSearch(osDescriptionDoc)
        c.addOpenSearch(o)

        if ('xml' == extension):
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c)
            return r.toString()
        else:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            return r.toString()

# /downloads.xml
#______________________________________________________________________________
class downloads:
    def GET(self, extension):
        solrUrl       = pubInfo['solr_base']+'&q='+pubInfo['query_base']+'&sort=month+desc&rows='+str(numRows)

        titleFragment = 'Most Downloaded Books in the last Month'
        urn           = pubInfo['urnroot'] + ':downloads'
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, solrUrl, urn, titleFragment=titleFragment)
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

# /new/0
#______________________________________________________________________________
class newest:
    def GET(self, start, extension):
        if extension == '.html':
            extension = 'html'
        else:
            extension = 'xml'

        if not start:
            start = 0
        else:
            if start.endswith('.html'):
                extension = 'html'
                start = start[:-5]
            start = int(start)


        solrUrl       = pubInfo['solr_base'] + '&q='+pubInfo['query_base']+'&sort=publicdate+desc&rows='+str(numRows)+'&start='+str(start*numRows)
        titleFragment = 'books sorted by update date'
        urn           = pubInfo['urnroot'] + ':new:%d' % (start)
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='/catalog/new/',
                                                titleFragment = titleFragment)
        c = ingestor.getCatalog()

        if 'html' == extension:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            return r.toString()
        else:
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True)
            return r.toString()

# /crawlable/0
#______________________________________________________________________________
class crawlable:
    def GET(self, start, extension):
        if extension == '.html':
            extension = 'html'
        else:
            extension = 'xml'

        if not start:
            start = 0
        else:
            if start.endswith('.html'):
                extension = 'html'
                start = start[:-5]
            start = int(start)

        crawlNumRows = 1000;
        solrUrl       = pubInfo['solr_base'] + '&q='+pubInfo['query_base']+'&rows='+str(crawlNumRows)+'&start='+str(start*crawlNumRows)
        titleFragment = '- crawlable feed'
        urn           = pubInfo['urnroot'] + ':crawl:%d' % (start)
        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=crawlNumRows,
                                                urlBase='/catalog/crawlable/',
                                                titleFragment = titleFragment)
        c = ingestor.getCatalog()

        if 'html' == extension:
            web.header('Content-Type', 'text/html')
            r = output.ArchiveCatalogToHtml(c, device = getDevice())
            return r.toString()
        else:
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True)
            return r.toString()


# /opensearch
#______________________________________________________________________________
class opensearch:
    def GET(self, query):
        params = cgi.parse_qs(web.ctx.query)

        if not 'start' in params:
            start = 0
        else:
            start = int(params['start'][0])

        q  = params['?q'][0]
        qq = urllib.quote(q)
        solrUrl       = pubInfo['solr_base'] + '&q='+qq+'+AND+'+pubInfo['query_base']+'&sort=month+desc&rows='+str(numRows)+'&start='+str(start*numRows)
        titleFragment = 'search results for ' + q
        urn           = pubInfo['urnroot'] + ':search:%s:%d' % (qq, start)

        ingestor = catalog.ingest.IASolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='opensearch?q=%s&start=' % (qq),
                                                titleFragment = titleFragment)

        c = ingestor.getCatalog()

        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(c, fabricateContentElement=True)
        return r.toString()

# /search
#______________________________________________________________________________
class htmlsearch:
    def GET(self, query):
        qs = web.ctx.query
        if qs.startswith('?'):
            qs = qs[1:]

        params = cgi.parse_qs(qs)

        if not 'start' in params:
            start = 0
        else:
            start = params['start'][0] # XXX hack for .html ending -- remove once fixed
            if start.endswith('.html'):
                start = start[:-5]
            start = int(start)

        q  = params['q'][0]
        qq = urllib.quote(q)
        solrUrl       = 'http://se.us.archive.org:8983/solr/select?q='+qq+'+AND+'+pubInfo['query_base']+'&fl=identifier,title,creator,oai_updatedate,date,contributor,publisher,subject,language,format&rows='+str(numRows)+'&start='+str(start*numRows)+'&wt=json'
        titleFragment = 'search results for ' + q
        urn           = pubInfo['urnroot'] + ':search:%s:%d' % (qq, start)

        ingestor = catalog.ingest.SolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='/search?q=%s&start=' % (qq), # XXX adding .html to end...
                                                titleFragment = titleFragment)

        c = ingestor.getCatalog()

        web.header('Content-Type', 'text/html')
        r = output.ArchiveCatalogToHtml(c, device = getDevice())
        return r.toString()

# /opensearch.xml - Open Search Description
#______________________________________________________________________________
class openSearchDescription:
    def GET(self):
        web.header('Content-Type', 'application/atom+xml')
        return """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Internet Archive Search</ShortName>
    <Description>Search archive.org's OPDS Catalog.</Description>
    <Url type="application/atom+xml"
        template="%s/opensearch?q={searchTerms}&amp;start={startPage?}"/>
</OpenSearchDescription>""" % (pubInfo['opdsroot'])


# redirect to remove trailing slash
#______________________________________________________________________________
class redirect:
    def GET(self, path):
        web.seeother('/' + path)

# redirect to index
#______________________________________________________________________________
class indexRedirect:
    def GET(self, path):
        web.seeother('/')


# main() - standalone mode
#______________________________________________________________________________
if __name__ == "__main__":
    #run in standalone mode
    app = web.application(urls, globals())
    app.run()
