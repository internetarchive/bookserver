Internet Archive Bookserver
===========================

This repository contains the ``bookserver`` package, which is useful for
working with OPDS catalog feeds. It also contains the source for the
http://bookserver.archive.org site.

To create a Catalog instance from scratch, you can use this code:

    >>> from bookserver import catalog
    >>> urn = 'urn:x-internet-archive:bookserver:catalog'
    >>> c = catalog.Catalog(title='Internet Archive OPDS', urn=urn)

To create a link to a free PDF:

    >>> l = catalog.Link(url   = 'http://archive.org/download/itemid/itemid.pdf',
    ...                  type  = 'application/pdf',
    ...                  rel   = 'http://opds-spec.org/acquisition')

To create a link to an html shopping cart that sells drm-ed books:

    >>> l2 = catalog.Link(url   = 'http://archive.org/download/drmbook/shoppingcart',
    ...                   type  = 'text/html',
    ...                   rel   = 'http://opds-spec.org/acquisition/buying',
    ...                   price = '10.00',
    ...                   currencycode = 'USD',
    ...                   formats = ('application/pdf;drm=acs', 'application/epub+zip;drm=acs'))

To create an entry for a book:

    >>> e = catalog.Entry({'urn'     : 'x-internet-archive:item:itemid',
    ...                    'title'   : u'test item',
    ...                    'updated' : '2009-01-01T00:00:00Z'}, links=[l])
    >>> c.addEntry(e)

    >>> e = catalog.Entry({'urn'     : 'x-internet-archive:item:drmbook',
    ...                    'title'   : u'A book with DRM',
    ...                    'updated' : '2009-01-01T00:00:00Z'}, links=[l2])
    >>> c.addEntry(e)

The catalog.Navigation class can help with creating prev and next rel links,
although you can just pass these in as args to __init__

    >>> start    = 0
    >>> numFound = 2
    >>> numRows  = 1
    >>> urlBase  = '/alpha/a/'
    >>> n = catalog.Navigation.initWithBaseUrl(start, numRows, numFound, urlBase)
    >>> c.addNavigation(n)

The catalog.OpenSearch class just holds OpenSearch Description Document for now:
    
    >>> osDescription = 'http://bookserver.archive.org/opensearch.xml'
    >>> o = catalog.OpenSearch(osDescription)
    >>> c.addOpenSearch(o)

From our Catalog instance, we can now create an OPDS feed in Atom format:
    
    >>> r = catalog.output.CatalogToAtom(c)
    >>> str = r.toString()

Different version of lxml will print xmlns differently (use ellipsis in doctest):

    >>> print str.rstrip() #doctest: +ELLIPSIS
    <feed ...
      <title>Internet Archive OPDS</title>
      <id>urn:x-internet-archive:bookserver:catalog</id>
      <updated>1970-01-01T00:00:00Z</updated>
      <link rel="self" type="application/atom+xml" href="http://bookserver.archive.org/catalog/"/>
      <author>
        <name>Internet Archive</name>
        <uri>http://www.archive.org</uri>
      </author>
      <link rel="search" type="application/opensearchdescription+xml" href="http://bookserver.archive.org/opensearch.xml"/>
      <link rel="next" type="application/atom+xml" href="/alpha/a/1" title="Next results"/>
      <entry>
        <title>test item</title>
        <id>x-internet-archive:item:itemid</id>
        <updated>2009-01-01T00:00:00Z</updated>
        <link href="http://archive.org/download/itemid/itemid.pdf" type="application/pdf" rel="http://opds-spec.org/acquisition"/>
      </entry>
      <entry>
        <title>A book with DRM</title>
        <id>x-internet-archive:item:drmbook</id>
        <updated>2009-01-01T00:00:00Z</updated>
        <link href="http://archive.org/download/drmbook/shoppingcart" type="text/html" rel="http://opds-spec.org/acquisition/buying">
          <opds:price currencycode="USD">10.00</opds:price>
          <dcterms:hasFormat>application/pdf;drm=acs</dcterms:hasFormat>
          <dcterms:hasFormat>application/epub+zip;drm=acs</dcterms:hasFormat>
        </link>
      </entry>
    </feed>
