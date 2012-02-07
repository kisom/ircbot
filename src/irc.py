# -*- coding: utf-8 -*-
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain
"""
IRC command support for the bot.
"""

import os
import re
from threading import Semaphore

IRC_MAXLEN = 4096
T_TUPLE = type(tuple())
T_LIST = type(list())


class Irc:
    def __init__(self, sock, server, port, user, channels):
        self.sock = sock
        self.slock = Semaphore(1)
        self.server = server
        self.port = port
        self.nick = user['nick']
        self.realname = user['realname']
        self.myhost = user['myhost']
        self.sysname = user['sysname']
        self.username = user['name']
        self.channels = channels


    def __dosync__(self, fn, *args):
        if not 0 == os.fork():
            return

        command = fn(args)
        self.slock.acquire()
        self.sock.send(command)
        self.slock.release()

        os._exit(os.EX_OK)

    def get_recipient(self, recipient):
        if type(recipient) == T_TUPLE or type(recipient) == T_LIST:
            recipient = ','.join(recipient)
        return recipient

    def msg(self, recipient, message):
        self.__dosync__(self.__msg__, recipient, message)

    def __msg__(self, recipient, message):
        command = 'PRIVMSG %s :%s\r\n' % (recipient, message)
        return command

    def action(self, recipient, message):
        command = 'ACTION ' + message
        self.msg(recipient, message)

    def pong(self, daemon):
        self.__dosync__(self.__pong__, daemon)

    def __pong__(self, daemon):
        command = 'PONG %s' % (daemon, )
        return command

    def quit(self):
        self.__dosync__(self.__quit__)

    def __quit__(self):
        return 'QUIT'

    def connect(self):
        self.sock.connect((self.server, self.port))
        self.sock.recv(4096)        # ignore server message
        time.sleep(5)
        self.sock.send('NICK %s\r\n' % (self.nick, ))
        user = 'USER %s %s %s %s\r\n' % (self.user, self.myhost, self.sysname,
                                         self.realname)
        time.sleep(5)
        self.sock.send(user)

        for channel in self.channels:
            command = 'JOIN %s\r\n' % (channel, )
            time.sleep(0.3)
            self.sock.send(command)

        self.sock.setblocking(0)

    def null_handler(self, data):
        return None

    def run(self, handler = self.null_handler):
        while True:
            data = self.sock.recv(IRC_MAXLEN)
            if (data.startswith('PING')):
                daemon = re.sub('^PING :([\\w.]+)', '\\1', data)
                self.pong(daemon)
            elif 0 == os.fork():
                handler(data)

    def __str__(self):
        return '%s:%d %s' % (self.server, self.port, ', '.join(self.channels))

