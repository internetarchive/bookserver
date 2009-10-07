#!/usr/bin/python2.5

#Copyright(c)2009 Internet Archive. Software license GPL version 3.

"""
This script is a proxy that formats solr queries as OPDS
"""

import sys
sys.path.append("/petabox/www/bookserver")

import web
import time
import string
import cgi
import urllib

import bookserver.catalog as catalog
import bookserver.catalog.output as output

numRows = 50

# You can customize pubInfo:
pubInfo = {
    'name'     : 'Internet Archive',
    'uri'      : 'http://www.archive.org',
    'opdsroot' : 'http://bookserver.archive.org/catalog',
    'mimetype' : 'application/atom+xml;profile=opds',
    'url_base' : '/catalog',
    'urnroot'  : 'urn:x-internet-archive:bookserver:catalog',
}

urls = (
    '/(.*)/',                       'redirect',
    '/alpha.(xml|html)',            'alphaList',
    '/alpha/(.)(?:/(.*))?',         'alpha',
    '/downloads.(xml|html)',        'downloads',
    '/new(?:/(.*))?',               'newest',
    '/opensearch.xml',              'openSearchDescription',
    '/opensearch(.*)',              'search',
    '/',                            'index',
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


# /
#______________________________________________________________________________
class index:
    def GET(self):

        datestr = getDateString()
        
        c = catalog.Catalog(
                            title     = 'Internet Archive OPDS',
                            urn       = pubInfo['urnroot'],
                            url       = pubInfo['opdsroot'],
                            datestr   = datestr,
                            author    = 'Internet Archive',
                            authorUri = 'http://www.archive.org',
                           )

        e = catalog.Entry({'title'  : 'Alphabetical By Title',
                           'urn'     : pubInfo['urnroot'] + ':titles:all',
                           'url'     : 'alpha.xml',
                           'updated' : datestr,
                           'content' : 'Alphabetical list of all titles.'
                         })
        c.addEntry(e)
        
        e = catalog.Entry({'title'   : 'Most Downloaded Books',
                           'urn'     : pubInfo['urnroot'] + ':downloads',
                           'url'     : 'downloads.xml',
                           'updated' : datestr,
                           'content' : 'The most downloaded books from the Internet Archive in the last month.'
                         })
        
        c.addEntry(e)
        
        e = catalog.Entry({'title'   : 'Recent Scans',
                           'urn'     : pubInfo['urnroot'] + ':new',
                           'url'     : 'new',
                           'updated' : datestr,
                           'content' : 'Books most recently scanned by the Internet Archive.'
                         })
        
        c.addEntry(e)
        
        osDescriptionDoc = 'http://bookserver.archive.org/catalog/opensearch.xml'
        o = catalog.OpenSearch(osDescriptionDoc)
        c.addOpenSearch(o)
        
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
           
            
        
        #TODO: add Image PDFs to this query
        solrUrl       = 'http://se.us.archive.org:8983/solr/select?q=firstTitle%3A'+letter+'*+AND+mediatype%3Atexts+AND+format%3A(LuraTech+PDF)&fl=identifier,title,creator,oai_updatedate,date,contributor,publisher,subject,language&sort=titleSorter+asc&rows='+str(numRows)+'&start='+str(start*numRows)+'&wt=json'
        titleFragment = 'books starting with "%s"' % (letter.upper())
        urn           = pubInfo['urnroot'] + ':%s:%d'%(letter, start)

        ingestor = catalog.ingest.SolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='/alpha/a/',
                                                titleFragment = titleFragment)
        c = ingestor.getCatalog()
    
        if 'html' == mode:
            web.header('Content-Type', 'text/html')
            r = output.CatalogToHtml(c)
            return r.toString()
        else:
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True, fabricateEpub=True)
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
                           )

        for letter in string.ascii_uppercase:
            lower = letter.lower()

            e = catalog.Entry({'title'   : 'Titles: ' + letter,
                               'urn'     : pubInfo['urnroot'] + ':titles:'+lower,
                               'url'     : self.alphaURL(extension, lower, 0),
                               'updated' : datestr,
                               'content' : 'Titles starting with ' + letter
                             })
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
            r = output.CatalogToHtml(c)
            return r.toString()

# /downloads.xml
#______________________________________________________________________________
class downloads:
    def GET(self, extension):
        #TODO: add Image PDFs to this query
        solrUrl = 'http://se.us.archive.org:8983/solr/select?q=mediatype%3Atexts+AND+format%3A(LuraTech+PDF)&fl=identifier,title,creator,oai_updatedate,date,contributor,publisher,subject,language,month&sort=month+desc&rows='+str(numRows)+'&wt=json'

        titleFragment = 'Most Downloaded Books in the last Month'
        urn           = pubInfo['urnroot'] + ':downloads'
        ingestor = catalog.ingest.SolrToCatalog(pubInfo, solrUrl, urn, titleFragment=titleFragment)
        c = ingestor.getCatalog()
        
        if ('xml' == extension):
            web.header('Content-Type', pubInfo['mimetype'])
            r = output.CatalogToAtom(c, fabricateContentElement=True, fabricateEpub=True)
            return r.toString()
        elif ('html' == extension):
            web.header('Content-Type', 'text/html')
            r = output.CatalogToHtml(c)
            return r.toString()
        else:
            web.seeother('/')

# /new/0
#______________________________________________________________________________
class newest:
    def GET(self, start):
        if not start:
            start = 0
        else:
            start = int(start)
        
        #TODO: add Image PDFs to this query
        solrUrl       = 'http://se.us.archive.org:8983/solr/select?q=mediatype%3Atexts+AND+format%3A(LuraTech+PDF)&fl=identifier,title,creator,oai_updatedate,date,contributor,publisher,subject,language&sort=updatedate+desc&rows='+str(numRows)+'&start='+str(start*numRows)+'&wt=json'
        titleFragment = 'books sorted by update date'
        urn           = pubInfo['urnroot'] + ':new:%d' % (start)
        ingestor = catalog.ingest.SolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='/new/',
                                                titleFragment = titleFragment)
        c = ingestor.getCatalog()
    
        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(c, fabricateContentElement=True, fabricateEpub=True)
        return r.toString()


# /search
#______________________________________________________________________________        
class search:
    def GET(self, query):
        params = cgi.parse_qs(web.ctx.query)

        if not 'start' in params:
            start = 0
        else:
            start = int(params['start'][0])

        q  = params['?q'][0]
        qq = urllib.quote(q)
        solrUrl       = 'http://se.us.archive.org:8983/solr/select?q='+qq+'+AND+mediatype%3Atexts+AND+format%3A(LuraTech+PDF)&fl=identifier,title,creator,oai_updatedate,date,contributor,publisher,subject,language&rows='+str(numRows)+'&start='+str(start*numRows)+'&wt=json'        
        titleFragment = 'search results for ' + q
        urn           = pubInfo['urnroot'] + ':search:%s:%d' % (qq, start)

        ingestor = catalog.ingest.SolrToCatalog(pubInfo, solrUrl, urn,
                                                start=start, numRows=numRows,
                                                urlBase='/opensearch?q=%s&start=' % (qq),
                                                titleFragment = titleFragment)

        c = ingestor.getCatalog()

        web.header('Content-Type', pubInfo['mimetype'])
        r = output.CatalogToAtom(c, fabricateContentElement=True, fabricateEpub=True)
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
        template="http://bookserver.archive.org/opensearch?q={searchTerms}&amp;start={startPage?}"/>
</OpenSearchDescription>"""        


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