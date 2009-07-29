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
This script downloads, installs, and configures the solr search engine.

'''


import commands
import os

solr_dir = '/solr' #beware! The custom scripts.conf (see below) contains a hardcoded path '/solr'!

print 'Installing Java6'
(ret, out) = commands.getstatusoutput("""/bin/echo -e 'sun-java6-bin shared/accepted-sun-dlj-v1-1 boolean true\nsun-java6-jre shared/accepted-sun-dlj-v1-1 boolean true' | sudo debconf-set-selections""")
assert 0 == ret

(ret, out) = commands.getstatusoutput("""DEBIAN_FRONTEND=noninteractive apt-get --force-yes -qq install sun-java6-bin sun-java6-jdk""")
print out
assert 0 == ret

if not os.path.exists('apache-solr-1.3.0.tgz'):
    print 'Downloading solr'
    (ret, out) = commands.getstatusoutput('wget -q http://mirrors.isc.org/pub/apache/lucene/solr/1.3.0/apache-solr-1.3.0.tgz')
    print out
    assert 0==ret

print 'Unpacking solr'
(ret, out) = commands.getstatusoutput('tar xzf apache-solr-1.3.0.tgz')
print out
assert 0==ret

if not os.path.exists(solr_dir):
    print 'creating solr_dir at ' + solr_dir
    ret = os.mkdir(solr_dir)

print 'copying solr example to solr_dir'
(ret, out) = commands.getstatusoutput("cp -r apache-solr-1.3.0/example '%s'" % (solr_dir))
print out
assert 0==ret

print 'adding custom schema.xml'
(ret, out) = commands.getstatusoutput("""wget -q -O '%s/example/solr/conf/schema.xml' 'http://home.us.archive.org/~rkumar/git/gitweb.cgi?p=bookserver/.git;a=blob_plain;f=aggregator/solr/schema.xml'""" % (solr_dir));
print out
assert 0==ret

print 'creating a solr user'
(ret, out) = commands.getstatusoutput("""adduser --system --no-create-home solr""")
print out
assert 0==ret

print 'adding custom scripts.conf.. BEWARE this file contains a hardcoded path to /solr'
(ret, out) = commands.getstatusoutput("""wget -q -O '%s/example/solr/conf/scripts.conf' 'http://home.us.archive.org/~rkumar/git/gitweb.cgi?p=bookserver/.git;a=blob_plain;f=aggregator/solr/scripts.conf'""" % (solr_dir));
print out
assert 0==ret

print 'adding solr start script'
(ret, out) = commands.getstatusoutput("""wget -q -O '%s/solr.sh' 'http://home.us.archive.org/~rkumar/git/gitweb.cgi?p=bookserver/.git;a=blob_plain;f=aggregator/solr/solr.sh'""" % (solr_dir));
print out
assert 0==ret

print 'adding solr upstart file'
(ret, out) = commands.getstatusoutput("""wget -q -O /etc/event.d/solr-upstart 'http://home.us.archive.org/~rkumar/git/gitweb.cgi?p=zolr/.git;a=blob_plain;f=solr-upstart'""");
print out
assert 0==ret

print 'changing ownership of solr_dir to solr role account'
(ret, out) = commands.getstatusoutput("""chown -R solr '%s'""" % (solr_dir));
print out
assert 0==ret

print 'setting u+x perms on solr_dir/solr.sh'
(ret, out) = commands.getstatusoutput("""chmod u+x '%s/solr.sh'""" % (solr_dir));
print out
assert 0==ret

