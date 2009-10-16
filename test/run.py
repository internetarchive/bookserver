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

import doctest
import glob
import commands

import sys
sys.path.append('..')

testfiles = glob.glob('*.txt')
testfiles.insert(0, '../README')

f = open('/etc/issue')
issue = f.read()
f.close()
if issue.startswith('Ubuntu 9.04'):
    #tests that depend on having the right version of lxml
    testfiles += glob.glob('*.jaunty')

for test in testfiles:
    (numFail, numTests) = doctest.testfile(test)
    print '%s: %d out of %d passed' % (test, (numTests - numFail), numTests)

    if numFail:
       print 'Rerunning test in verbose mode!'
       doctest.testfile(test, verbose=True)

testmodules =  glob.glob('../bookserver/*.py')
testmodules += glob.glob('../bookserver/catalog/*.py')

for test in testmodules:
    if test.endswith('catalog/__init__.py'):
        continue
        
    (status, output) = commands.getstatusoutput('python ' + test)
    print 'testing module %s' % (test)
    if '' != output:
        print output

    if (0 != status) or ('' != output):
        print 'Rerunning test in verbose mode!'
        (status, output) = commands.getstatusoutput('python ' + test + ' -v')
        print output
