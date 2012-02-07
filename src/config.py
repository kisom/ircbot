# -*- coding: utf-8 -*-
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain
"""
Provide configuration file support for the IRC bot. Allows separation of
configuration file type from the main code.`
"""


import simplejson


def load(configfile):
    """
    Load a config file and parse it.
    """
    rawconfig = open(configfile).read()

    cfg = simplejson.loads(rawconfig)
    return cfg
