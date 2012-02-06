#!/usr/bin/env python

import datetime
import os
import re
import socket
import sys
import time

conf_fn             = './logger-config'
config              = { }
irc                 = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
message_handlers    = None

def load_config(config_file):
    try:
        f = open(config_file)
        for line in f.readlines():
            strip = line.strip()
            if strip.startswith('#'): continue      # ignore comments
            if strip == '':           continue      # ignore blank lines

            if len(strip.split(':')) < 2: continue  # ensure valid configs
            key, value = strip.split(':', 1)        # allow colons in values

            config[key] = value.strip()             # load value to hash

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
        print 'missing user!'
        return False
    if not 'server' in config:
        print 'missing server!'
        return False
    
    # port requires special handling
    if not 'port' in config:
        config['port'] = 6667
    else:
        config['port'] = int(config['port'])
        
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
        irc.settimeout(5)
        irc.connect((config['server'], config['port']))
        irc.setblocking(1)
    
    except socket.timeout:
        print 'socket timeout!'
        return False
    except TypeError:
        print 'server must be string and port must be an integer!'
        return False
    
    irc.recv(4096)                                  # discard server message
    time.sleep(5)
    print 'sending nick...'
    irc.send( irc_send(['NICK', config['nick']]) )  # send nickname
                                                    # send username
    time.sleep(5)
    print 'sending user...'
    irc.send( irc_send(['USER', config['user'], config['myhost'],
                        config['sname'], config['realname']] ))
    for channel in config['channels']:              # join channels
        time.sleep(0.3)
        print "joining channel %s" % channel
        irc.send( irc_send(['JOIN', channel]) )
    
    irc.setblocking(0)
    
    return irc

def basic_console():
    while True:
        try:
            irc.setblocking(1)
            line  = raw_input('>')
    
            data  = '%s\r\n' % line
            irc.send(data)
    
            data = irc.recv(4096)
            if data: print data
            irc.setblocking(0)
        except KeyboardInterrupt:
            irc.close()
            sys.exit(0)
    

def process_data(data):
    if not 0 == os.fork():
        return

    if data.startswith('PING'):
        sender      = re.sub('^PING :([\\w.]+)', '\\1', data)
        print 'sending PONG...'
        irc.send( irc_send(['PONG', sender]))
    elif 'PRIVMSG' in data:
        sender      = re.sub('^:(.+)\!.* PRIVMSG.*', '\\1', data).strip()
        channel     = re.sub('^.* PRIVMSG ([#-_\\w]+) :.*$', '\\1', 
                             data).strip()
        message     = re.sub('^.* PRIVMSG [#-_\\w]+ :(.+)$', '\\1', 
                             data).strip()
        if channel == config['nick']:
            print '/msg detected...'
            channel = sender
        
        if channel.startswith(':'):
            os._exit(os.EX_OK)

        try:
            log = open('irclogs/%s.log' % channel, 'a')
        except IOError as e:
            print 'error writing: \n\t%s\n\t%s\n\t%s\n' % (channel, message,
                                                           sender)
            pass
        else:
            log.write('(%s) %s: %s\n' % (datetime.datetime.now(), 
                                         sender, message))
            print '(%s) %s %s: %s' % (datetime.datetime.now(), channel, 
                                      sender, message)
            log.close()
    os._exit(os.EX_OK)

if __name__ == '__main__':
    load_config(conf_fn)
    irc = connect()

    if not irc:
        exit(0)

    irc.setblocking(1)
    print 'running...'
    while True:
        try:
            data = irc.recv(4096)
            if data:
                process_data(data)
        except KeyboardInterrupt:
            basic_console()
        except socket.error, e:
            if e.errno == 11:
                raise
            
    
