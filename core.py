#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain
"""
Core code for IRC logging bot.
"""

import daemon
import imp
import os
import sys

from src import config
from src import irc


DEFAULT_CONFIG = 'config.json'


def valid_userp(user):
    """Validate a user."""
    valid_user_keys = ['realname', 'name', 'nick', 'myhost', 'sysname']
    if not user:
        return False
    if sorted(valid_user_keys) == sorted(user.keys()):
        return True
    return False


def setup_connection(server, user):
    """Set up an IRC connection."""
    host = server['host']
    port = server['port']
    channels = server['channels']

    assert(not host == None)
    assert(not port == None)
    assert(not channels == [])
    assert(valid_userp(user))

    return irc.Irc(host, port, user, channels)


def init(configfile):
    """Load configuration and load IRC connections."""
    cfg = config.load(configfile)

    if 'user' in cfg:
        defaultuser = cfg['user']
    else:
        defaultuser = None

    if not 'servers' in cfg:
        print 'No servers specified in %s - cannot proceed!' % (configfile,)
        exit(1)

    servers = []
    handlers = []
    for server in cfg['servers']:
        if not 'user' in server:
            user = defaultuser
        else:
            user = cfg['user']

        if 'handler' in server:
            if 'module' == server['handler']['type']:
                modname = server['handler']['name']
                fptr, pathname, description = imp.find_module(
                                                    modname,
                                                    ['plugins/'])
                modtop = imp.load_module(modname, fptr, pathname,
                                         description)
                fptr.close()
                handler = modtop.main
            elif 'function' == server['handler']['type']:
                handler = eval(server['handler']['name'])
        else:
            handler = irc.null_handler

        servers.append(setup_connection(server, user))
        handlers.append(handler)

    return servers, handlers


def run(servers, handlers):
    """Daemonise and run IRC connections."""

    print '%d servers loaded...' % (len(servers), )
    assert(len(servers) == len(handlers))
    context = daemon.DaemonContext(working_directory=os.getcwd())
    logdir = os.path.join(os.getcwd(), 'logs/')

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    context.stdout = open(logdir + 'core.log', 'w')
    context.stderr = open(logdir + 'core.err', 'w')

    with context:
        for n in range(len(servers)):
            print 'connecting:', servers[n]
            if 0 == os.fork():
                server = servers[n]
                handler = handlers[n]
                server.connect()
                server.run(handler=handler)
                os._exit(os.EX_IOERR)


def main(configfile):
    """Set up and run the connections."""
    servers, handlers = init(configfile)
    run(servers, handlers)


if '__main__' == __name__:
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(DEFAULT_CONFIG)
