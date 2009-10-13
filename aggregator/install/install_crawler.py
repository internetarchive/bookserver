#!/usr/bin/python

'''
Copyright(c)2009 Internet Archive. Software license AGPL version 3.

This file is part of IA Bookserver.

    IA Bookserver is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    IA Bookserver is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with IA Bookserver.  If not, see <http://www.gnu.org/licenses/>.
    
'''    

'''
This script downloads, installs, and configures the OPDS crawler.
'''

import commands
import os

crawler_dir = '/crawler'
warc_dir    = crawler_dir + '/data'

def cmd(description, command):
    print description
    (ret, out) = commands.getstatusoutput(command)
    print out
    assert 0 == ret
    

print 'installing build-essential, swig, and svn'
(ret, out) = commands.getstatusoutput("""DEBIAN_FRONTEND=noninteractive apt-get --force-yes -qq install build-essential subversion swig1.3""")
print out
assert 0 == ret

print 'installing warc-tools'
if not os.path.exists('/tmp/warc-tools'):
    (ret, out) = commands.getstatusoutput('svn checkout http://warc-tools.googlecode.com/svn/trunk/ /tmp/warc-tools')
    print out
    assert 0==ret

print 'patching warc-tools makefile'
(ret, out) = commands.getstatusoutput("""wget -q -O /tmp/warc-tools/makefile 'http://home.us.archive.org/~rkumar/git/gitweb.cgi?p=bookserver/.git;a=blob_plain;f=aggregator/install/warc-tools-makefile-64bit'""");
print out
assert 0==ret
    
print 'building and installing warc-tools'
(ret, out) = commands.getstatusoutput("""make -C /tmp/warc-tools install""");
print out
assert 0==ret

print 'installing python-feedparser, python-lxml, python-simplejson, and curl'
(ret, out) = commands.getstatusoutput("""DEBIAN_FRONTEND=noninteractive apt-get --force-yes -qq install python-feedparser python-lxml python-simplejson curl""")
print out
assert 0==ret

cmd('installing greenlet', """DEBIAN_FRONTEND=noninteractive apt-get --force-yes -qq install python-codespeak-lib""")

cmd('installing eventlet', 'easy_install eventlet')

cmd('installing python-xml', 'DEBIAN_FRONTEND=noninteractive apt-get --force-yes -qq install python-xml')

cmd('installing opensearch.py', 'easy_install opensearch')

if not os.path.exists(warc_dir):
    print 'making warc_dir ' + warc_dir
    os.makedirs(warc_dir)
    