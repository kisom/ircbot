# -*- coding: utf-8 -*-
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain
"""
Log incoming messages.
"""


import datetime
import os
import re


LOGDIR = os.path.join(os.getcwd(), 'logs')
SRVRE = r'^([\w.-])+ .+$'
CHANRE = r'^.* PRIVMSG ([#-_\w]+) :.*$'
MSGRE = r'^.* PRIVMSG [#-_\w]+ :(.+)$'


def filename(server, channel):
    """Build the filename for a log."""
    servername = re.sub(r'^.+\.(\w+)\.\w{2,5}$', r'\1', server)
    return os.path.join(LOGDIR, servername, '%s.log' % (channel, ))


def log_message(server, channel, sender, message):
    """Write a message to the appropriate log."""
    path = filename(server, channel)

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    logfile = open(filename(server, channel), 'a')
    now = datetime.datetime.utcnow()

    logstr = '%s %s: %s\n' % (now, sender, message)
    logfile.write(logstr)
    logfile.close()


def main(data, conn):
    """
    Receive incoming messages and log them.
    """

    data_arr = data.split(' ')
    command = data_arr[1]

    if command == 'PRIVMSG':
        sender = re.sub('^:(.+)\!.* PRIVMSG.*', '\\1', data).strip()
        channel = re.sub(CHANRE, r'\1', data).strip()
        message = re.sub(MSGRE, r'\1', data).strip()
        server = conn.server

        if channel == conn.nick:
            channel = sender

        if 0 == os.fork():
            log_message(server, channel, sender, message)
            os._exit(os.EX_OK)
