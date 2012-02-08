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


def null_handler(data, conn):
    """Take data and display it."""
    print data


class Irc:
    """
    Model an IRC connection.
    """
    sock = None
    slock = None
    server = None
    port = None
    nick = None
    realname = None
    myhost = None
    sysname = None
    username = None
    channels = None


    def __init__(self, server, port, user, channels):
        """
        Initialise an IRC connection. Requires a server, a port, a dictionary
        of user values (name, nick, realname, sysname, and myhost), and a list
        of channels.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
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

        command = fun(*args)
        self.slock.acquire()
        self.sock.send(command)
        self.slock.release()

        os._exit(os.EX_OK)

    def connectedp(self):
        connected = True
        self.slock.acquire()
        try:
            self.sock.getpeername()
        except socket.error as err:
            connected = False
        finally:
            self.slock.release()
        return connected


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
        command = 'PONG %s' % (daemon, )
        return command

    def quit(self):
        """Send a quit."""
        self.__dosync__(self.__quit__)

    def __quit__(self):
        """Send a quit command to the server."""
        return 'QUIT'

    def raw(self, command):
        """Allow sending raw IRC commands."""
        self.__dosync__(lambda : command)

    def connect(self):
        """Connect to the server."""
        self.slock.acquire()
        self.sock.setblocking(1)
        self.sock.connect((self.server, self.port))

        time.sleep(5)
        self.sock.send('NICK %s\r\n' % (self.nick, ))
        user = 'USER %s %s %s %s\r\n' % (self.username, self.myhost,
                                         self.sysname, self.realname)
        self.sock.recv(IRC_MAXLEN) 
        self.sock.send(user)

        time.sleep(1)
        try:
            self.sock.settimeout(1)
            while self.sock.recv(IRC_MAXLEN):
                time.sleep(0.1)
        except socket.timeout:
            pass
 
        for channel in self.channels:
            command = 'JOIN %s\r\n' % (channel, )
            time.sleep(0.3)
            self.sock.send(command)

        self.sock.settimeout(None)
        self.slock.release()


    def reconnect(self):
        """Drop the connection and reconnect."""
        self.quit()
        time.sleep(3)
        self.connect()


    def run(self, handler=null_handler):
        """Kick of the run loop. Will run until a socket error crops up."""
        while True:
            sys.stdout.flush()
            sys.stderr.flush()
            try:
                data = self.syncread()
            except socket.error as err:
                sys.stderr.write('%s\n\t%s\n' % (self, err))
                if not 11 == err.errno:
                    time.sleep(0.5)     # give the socket time to recover
                    continue
                break
            except KeyboardInterrupt:
                self.sock.close()
                break
            except Exception as err:
                sys.stderr.write('Exception: %s\n' % (err, ))
            open('logs/raw.log', 'w+').write('%s\n' % (data, ))
            if data.startswith('PING'):
                daemon = re.sub('^PING :([\\w.]+)', '\\1', data)
                self.pong(daemon)
            else:
                while not self.__handler(handler, data):
                    pass

    def __handler(self, handler, data):
        """
        Run the handler
        """
        try:
            if not 0 == os.fork():
                return True
            handler(data, self)
            os._exit(os.EX_OK)
        except OSError as err:
            return False
        else:
            return False
        
