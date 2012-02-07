# -*- coding: utf-8 -*-
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain
"""
IRC command support for the bot.
"""

import os
import re
import socket
import sys
import time
import threading

IRC_MAXLEN = 4096
T_TUPLE = type(tuple())
T_LIST = type(list())


def get_recipient(recipient):
    """
    Convert a list of recipients to a proper string.
    """
    if type(recipient) == T_TUPLE or type(recipient) == T_LIST:
        recipient = ','.join(recipient)
    return recipient


def null_handler(data):
    """Take data and display it."""
    print data


class Irc:
    """
    Model an IRC connection.
    """
    def __init__(self, server, port, user, channels):
        """
        Initialise an IRC connection. Requires a server, a port, a dictionary
        of user values (name, nick, realname, sysname, and myhost), and a list
        of channels.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.slock = threading.Semaphore(1)
        self.server = server
        self.port = port
        self.nick = user['nick']
        self.realname = user['realname']
        self.myhost = user['myhost']
        self.sysname = user['sysname']
        self.username = user['name']
        self.channels = channels

    def __str__(self):
        """String representation is in the form server:port <channel list>"""
        return '%s:%d %s' % (self.server, self.port, ', '.join(self.channels))

    def syncread(self):
        """
        Synchronously read the socket using the semaphore.
        """
        self.slock.acquire()
        data = self.sock.recv(IRC_MAXLEN)
        self.slock.release()
        return data

    def __dosync__(self, fun, *args):
        """Apply args to the fn to retrieve a command, then send it on the
        socket using semaphore locking."""
        if not 0 == os.fork():
            return

        command = fun(args)
        self.slock.acquire()
        self.sock.send(command)
        self.slock.release()

        os._exit(os.EX_OK)

    def msg(self, recipient, message):
        """Send a privmsg to recipient."""
        self.__dosync__(self.__msg__, recipient, message)

    def __msg__(self, recipient, message):
        """Return an appropriate PRIVMSG command for __dosync__"""
        command = 'PRIVMSG %s :%s\r\n' % (recipient, message)
        return command

    def action(self, recipient, message):
        """Send an action to recipient."""
        command = 'ACTION %s' % (message, )
        self.msg(recipient, command)

    def pong(self, daemon):
        """Reply to a PING request."""
        self.__dosync__(self.__pong__, daemon)

    def __pong__(self, daemon):
        """Return an appropriate PING command."""
        print '__pong__: ', daemon
        command = 'PONG %s' % (daemon, )
        return command

    def quit(self):
        """Send a quit."""
        self.__dosync__(self.__quit__)

    def __quit__(self):
        """Send a quit command to the server."""
        return 'QUIT'

    def connect(self):
        """Connect to the server."""
        self.sock.connect((self.server, self.port))
        self.sock.recv(4096)        # ignore server message
        time.sleep(5)
        self.sock.send('NICK %s\r\n' % (self.nick, ))
        user = 'USER %s %s %s %s\r\n' % (self.username, self.myhost,
                                         self.sysname, self.realname)
        time.sleep(5)
        self.sock.send(user)

        for channel in self.channels:
            command = 'JOIN %s\r\n' % (channel, )
            time.sleep(0.3)
            self.sock.send(command)

        self.sock.setblocking(1)

    def run(self, handler=null_handler):
        """Kick of the run loop. Will run until a socket error crops up."""
        while True:
            try:
                data = self.syncread()
                print data
            except socket.error as err:
                if not 11 == err.errno:
                    time.sleep(0.5)     # give the socket time to recover
                    continue
                sys.stderr.write('%s\n\t%s\n' % (self, err))
                break
            except KeyboardInterrupt:
                self.sock.close()
                break
            except Exception as err:
                sys.stderr.write('Exception: %s\n' % (err, ))
            if (data.startswith('PING')):
                print 'top: ping'
                daemon = re.sub('^PING :([\\w.]+)', '\\1', data)
                self.pong(daemon)
            elif 0 == os.fork():
                handler(data)
                os._exit(os.EX_OK)      # clean up if the handler doesn't
