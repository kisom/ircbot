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
CHANRE = r'^.* PRIVMSG ([#-_\w]+) :.*$'
MSGRE = r'^.* PRIVMSG [#-_\w]+ :(.+)$'

def main(data, conn):
    """
    Receive incoming messages and log them.
    """

    data_arr = data.split(' ')
    if data_arr[1] == 'PRIVMSG':
        sender = re.sub('^:(.+)\!.* PRIVMSG.*', '\\1', data).strip()
        channel = re.sub(CHANRE, r'\1', data).strip()
        message = re.sub(MSGRE, r'\1', data).strip()

        print '[*] logger: (%s) %s' % (channel, message)
        conn.msg(channel, message)


        
