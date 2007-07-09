# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id$
# =============================================================================
#             $URL$
# $LastChangedDate$
#             $Rev$
#   $LastChangedBy$
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
import os
import sys
import pygtk
import irclib
import pynotify
try:
    pynotify.init("Markup")
except Exception, error:
    print "Failed to init python-notify 'Markup'"
    print error

pygtk.require('2.0')

IRC_CODES_RE = re.compile(
    ur'(\\x16|\\x02|\\x1f|\\x0f|\\x[a|c]\d{1}|' + \
    ur'\\x03((\d{1,2},\d{1,2})|(\d{1,2}))?)',
    re.IGNORECASE
)

#irclib.DEBUG = True
class IrssiProxyNotifier:

    def __init__(self,passwd, name='', timeout=5, proxies=[], friends=[]):
        self.passwd = passwd
        self.name = name
        self.timeout = timeout
        self.proxies = proxies
        self.friends = friends
        self.irc = irclib.IRC()
        self.nicks = []
        # We should only need to handle these
        self.irc.add_global_handler('privmsg', self.handle_private_messages)
        self.irc.add_global_handler('pubmsg', self.handle_public_messages)
        self.irc.add_global_handler('join', self.handle_joins)
        self.irc.add_global_handler('part', self.handle_parts)
        self.irc.add_global_handler('quit', self.handle_quits)
        self.irc.add_global_handler('nick', self.handle_nicks)

    def notify(self, message, header='Irssi Notifier'):
        if isinstance(message, list):
            message = ' '.join(message).strip()
        uri = os.path.join(os.path.dirname(__file__), 'irssi_mini.png')
        notification = pynotify.Notification(header, message.strip(), uri)
        notification.set_timeout(self.timeout)
        notification.show()

    def _strip_irc_codes(self, message):
        return eval(re.sub(IRC_CODES_RE, '', repr(message)))

    def handle_private_messages(self, connection, event):
        nick = event.source().split('!')[0]
        if nick not in self.nicks:
            header = "<b>New Private IRC Message:</b>\n"
            message = self._strip_irc_codes(' '.join(event.arguments()).strip())
            message = "<b>From <i>%s</i><tt>(%s)</tt>:</b>\n%s" % \
                    (
                        event.source().split('!')[0],
                        connection.get_server_name().rstrip('.proxy'),
                        message
                    )
            self.notify(header + message)

    def handle_public_messages(self, connection, event):
        header = "<b>New IRC Message:</b>\n"
        message = self._strip_irc_codes(' '.join(event.arguments()).strip())
        notify = False
        # Are we addressed directly
        for nick in self.nicks:
            if message.startswith(nick):
                message = message[len(nick)+1:].strip()
                notify = True
            # Are we instead mentioned in the message
            elif message.find(nick) != -1:
                notify = True
        # Should we notify
        if notify:
            message = "<b>From <i>%s</i> on <tt>%s(%s)</tt>:</b>\n%s" % \
                (
                    event.source().split('!')[0],
                    event.target(),
                    connection.get_server_name().rstrip('.proxy'),
                    message
                )
            self.notify(header + message)

    def handle_joins(self, connection, event):
        nick = event.source().split('!')[0]
        if nick in self.friends:
            header = '<b>Known Friend Has Joined:</b>\n'
            message = '%s joined %s on %s' % (
                nick,
                event.target(),
                connection.get_server_name().rstrip('.proxy')
            )
            self.notify( header + message )

    def handle_parts(self, connection, event):
        nick = event.source().split('!')[0]
        if nick in self.friends:
            header = '<b>Known Friend Has Parted:</b>\n'
            message = '%s parted %s on %s' % (
                nick,
                event.target(),
                connection.get_server_name().rstrip('.proxy')
            )
            self.notify( header + message )

    def handle_quits(self, connection, event):
        nick = event.source().split('!')[0]
        if nick in self.friends:
            self.notify("%r has quit!" % nick)

    def handle_nicks(self, connection, event):
        header = "<b>Known Friend Changed Nick:</b>\n"
        newnick = event.target()
        oldnick = event.source().split('!')[0]
        if (oldnick or newnick) in self.friends:
            message = "From %r to %r on %r" % (
                oldnick, newnick, connection.get_server_name().rstrip('.proxy')
            )
            self.notify( header + message )

    def connect(self):
        for server, port, nick in self.proxies:
            self.nicks.append(nick)

            try:
                connection = self.irc.server().connect(
                    server,
                    port,
                    nick,
                    username = self.name,
                    password = self.passwd
                )
                if connection.connected:
                    self.notify(
                        "<b>Connection Sucessfull:</b>\n" + \
                        "To irssi proxy on %s:%s" % ( server, port )
                    )
                else:
                    self.notify(
                        "<b>Connection Failed:</b>\n" + \
                        "Failed to connect to %s:%s" % ( server, port )
                    )
            except irclib.ServerConnectionError, error:
                print error
                sys.exit(1)

    def start(self):
        self.notify("Now Listening...")
        self.irc.process_forever()

    def quit(self):
        self.irc.disconnect_all()
        self.notify("Exited")
