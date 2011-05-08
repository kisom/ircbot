#!/usr/bin/env python

import socket
import sys

conf_fn     = './config'
config      = { }

def load_config(config_file):
    try:
        f = open(config_file)
        for line in f.readlines():
            strip = line.strip()
            if strip.startswith('#'): continue      # ignore comments
            if strip == '':           continue      # ignore blank lines

            if len(strip.split(':')) < 2: continue  # ensure valid configs
            key, value = strip.split(':', 1)        # allow colons in values

            config[key] = value                     # load value to hash

    except IOError, e:
        print str(e)
        sys.exit(0)

def irc_send(message):
    msg = ' '.join(message)
    msg = '%s\r\n' % msg
    
    return msg

def connect():
    # fail if we're missing critical config data
    if not 'user' in config:
        return False
    if not 'server' in config:
        return False
    if not 'port' in config:
        config['port'] = 6667
        
    # load defaults for missing config data
    if not 'user' in config:
        config['nick'] = config['user']
    if not 'myhost' in config:
        config['myhost'] = config['example.net']
    if not 'sname' in config:
        config['sname'] = config['user']
    if not 'realname' in config:
        config['realname'] = config['user']
    if not 'channels' in config:
        config['channels'] = [ '%s_master' % config['user'] ]
    else:
        config['channels'] = config['channels'].split(' ')
        
    try:
        irc = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        irc.settimeout(3)
        
        irc.connect( (config['server'], config['port']))
    
    except socket.timeout:
        return False
    except TypeError:
        print 'server must be string and port must be an integer!'
        return False
    
    irc.recv(4096)                                  # discard server message
    irc.send( irc_send(['NICK', config['nick']]) )  # send nickname
                                                    # send username
    irc.send( irc_send(['USER', config['user'], config['myhost'],
                        config['sname'], config['realname']] ))
    for channel in config['channels']:              # join channels
        irc.send( irc_send(['JOIN', channel]) )
        irc_send( irc_send(['PRIVMSG', channel, ':hey guys']) )
    