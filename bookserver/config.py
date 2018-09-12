#!/usr/bin/env python
#-*-coding: utf-8 -*-
#Copyright(c) 2017 Internet Archive. Software license AGPL

import os
import sys
import types
import ConfigParser

path = os.path.dirname(os.path.realpath(__file__))
approot = os.path.abspath(os.path.join(path, os.pardir))

def getdef(self, section, option, default_value):
    try:
        return self.get(section, option)
    except:
        return default_value

config = ConfigParser.ConfigParser()
config.read('%s/config.cfg' % path)
config.getdef = types.MethodType(getdef, config)

PROTOCOL = config.getdef("server", "protocol", 'https')
HOST = config.getdef("server", "host", 'bookserver.archive.org')
PORT = int(config.getdef("server", "port", 443))
DEBUG = bool(int(config.getdef("server", "debug", 0)))
