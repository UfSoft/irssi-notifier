# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: notifier.py 45 2007-09-04 08:00:12Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/notifier.py $
# $LastChangedDate: 2007-09-04 09:00:12 +0100 (Tue, 04 Sep 2007) $
#             $Rev: 45 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
import os
from cgi import escape as cgi_escape
import sys
import xss          # This is used to know how long X has been idle
                    # http://bebop.bigasterisk.com/python
import pygtk
import irclib
import pynotify
import threading    # This package is used to setup a timer
try:
    pynotify.init("Markup")
except Exception, error:
    print "Failed to init python-notify 'Markup'"
    print error

pygtk.require('2.0')

#from irssinotifier.translation import _


IRC_CODES_RE = re.compile(
    #ur'(\\x16|\\x02|\\x1f|\\x0f|\\x[a|c]\d{1}|' + \
    ur'(\\x02|\\x07|\\x0f|\\x16|\\1d|\\1f|' + \
    ur'\\x03((\d{1,2},\d{1,2})|(\d{1,2}))?)',
    re.IGNORECASE
)

class IrssiProxyNotifier:

    def __init__(self,passwd, name='', timeout=5, proxies=[], friends=[],
                 x_away=0, away_reason="", bitlbee=False, charset='latin1'):
        self.passwd = passwd
        self.name = name
        self.timeout = timeout
        self.proxies = proxies
        self.friends = friends
        self.x_away = x_away
        self.away_reason = away_reason
        self.bitlbee = bitlbee
        self.timer = None
        self.charset = charset
        self.irc = irclib.IRC()
        self.nicks = []
        # We should only need to handle these
        self.irc.add_global_handler('privmsg', self.handle_private_messages)
        self.irc.add_global_handler('pubmsg', self.handle_public_messages)
        self.irc.add_global_handler('join', self.handle_joins)
        self.irc.add_global_handler('part', self.handle_parts)
        self.irc.add_global_handler('quit', self.handle_quits)
        self.irc.add_global_handler('nick', self.handle_nicks)
        self.irc.add_global_handler('action', self.handle_action_messages)
        self.irc.add_global_handler('mode', self.handle_modes) # for bitlbee
        #  This sets up handlers for away events, and loads the X idle tracker
        if self.x_away:
            self.idle = False
            self.away = False
            self.awaybecauseidle = False
            self.irc.add_global_handler('nowaway', self.handle_away)
            self.irc.add_global_handler('unaway', self.handle_away)
            self.tracker = xss.IdleTracker(idle_threshold=x_away)

    # TRANSLATOR: No need to translate the app name, just leave it blank
    def notify(self, message, header=_('Irssi Notifier')):
        if isinstance(message, list):
            message = u' '.join(message).strip()

        # First we try UTF-8. If the message is not valid, then we try the
        # default fallback charset.
        if not isinstance(message, unicode):
            try:
                message = unicode(message, 'utf-8')
            except UnicodeDecodeError:
                message = unicode(message, self.charset)

        uri = os.path.join(os.path.dirname(__file__), 'data', 'irssi_mini.png')
        notification = pynotify.Notification(header, message.strip(), uri)
        notification.set_timeout(self.timeout)
        notification.show()

    def _strip_irc_codes(self, message):
        return cgi_escape(eval(re.sub(IRC_CODES_RE, '', repr(message))))

    def _addressing_ownnick(self, event):
        nick = event.source().split('!')[0]
        message = self._strip_irc_codes(' '.join(event.arguments()).strip())
        return nick in message

    def handle_private_messages(self, connection, event):
        nick = event.source().split('!')[0]
        if nick not in self.nicks:
            header = _("<b>New Private Message:</b>\n")
            message = self._strip_irc_codes(' '.join(event.arguments()).strip())
            message = _("<b>From <i>%(nick)s</i><tt>(%(server)s)</tt>:"
                        "</b>\n%(message)s") % \
                    {'nick': event.source().split('!')[0],
                     'server': connection.get_server_name().rstrip('.proxy'),
                     'message': message }
            self.notify(header + message)

    def handle_public_messages(self, connection, event):
        header = _("<b>New Message:</b>\n")
        message = self._strip_irc_codes(' '.join(event.arguments()).strip())
        notify = False

        if not self._addressing_ownnick(event):
            # Are we addressed directly
            for nick in self.nicks:
                if message.startswith(nick):
                    message = message[len(nick)+1:].strip()
                    notify = True
                    # Are we instead mentioned in the message
                elif message.find(nick) != -1:
                    notify = True

        if notify:
            message = _("<b>From <i>%(nick)s</i> on <tt>%(channel)"
                        "s(%(server)s)</tt>:</b>\n%(message)s") % \
                {'nick': event.source().split('!')[0],
                 'channel': event.target(),
                 'server': connection.get_server_name().rstrip('.proxy'),
                 'message': message }
            self.notify(header + message)

    def handle_action_messages(self, connection, event):
        header = _("<b>New IRC Action:</b>\n")
        message = self._strip_irc_codes(' '.join(event.arguments()).strip())
        notify = False
        if not self._addressing_ownnick(event):
            for nick in self.nicks:
                if nick in message:
                    notify = True

        if notify:
            message = _("<b>From <i>%(nick)s</i> on <tt>%(channel)s"
                        "(%(server)s)</tt>:</b>\n%(message)s") % \
                {'nick': event.source().split('!')[0],
                 'channel': event.target(),
                 'server': connection.get_server_name().rstrip('.proxy'),
                 'message': '<i>%s %s</i>' % (event.source().split('!')[0],
                                              message)}
            self.notify(header + message)


    def handle_joins(self, connection, event):
        nick = event.source().split('!')[0]
        if nick in self.friends:
            header = _('<b>Known Friend Has Joined:</b>\n')
            message = _('%(nick)s joined %(channel)s on %(server)s') % {
                'nick': nick,
                'channel': event.target(),
                'server': connection.get_server_name().rstrip('.proxy') }
            self.notify( header + message )

    def handle_parts(self, connection, event):
        nick = event.source().split('!')[0]
        if nick in self.friends:
            header = _('<b>Known Friend Has Parted:</b>\n')
            message = _('%(nick)s parted %(channel)s on %(server)s') % {
                'nick': nick,
                'channel': event.target(),
                'server': connection.get_server_name().rstrip('.proxy')}
            self.notify( header + message )

    def handle_quits(self, connection, event):
        nick = event.source().split('!')[0]
        if nick in self.friends:
            self.notify(_("%(nick)r has quit!") % {'nick': nick})

    def handle_nicks(self, connection, event):
        header = _("<b>Known Friend Changed Nick:</b>\n")
        newnick = event.target()
        oldnick = event.source().split('!')[0]
        if (oldnick or newnick) in self.friends:
            message = _("From %(oldnick)r to %(newnick)r on %(server)r") % {
                'oldnick': oldnick,
                'newnick': newnick,
                'server': connection.get_server_name().rstrip('.proxy')}
            self.notify( header + message )

    # This function handles modes changes to know who has come online on
    # bitlbee. A friend is online if he has mode +v on the &bitlbee channel.
    def handle_modes(self, connection, event):
        sourcenick = event.source().split('!')[0]
        if (self.bitlbee and event.target() == "&bitlbee"
        and sourcenick == "root"):
            modes = irclib.parse_channel_modes(' '.join(event.arguments()))
            for mode in modes:
                if mode[1] == "v" and mode[0] == "+":
                    header = _('<b>Contact Is Online</b>\n')
                    message = _('%(nick)s has come online on bitlbee') % {
                        'nick': mode[2] }
                    self.notify( header + message )

    # This functions handles updates the away attributes according to what the
    # server tells us.
    def handle_away(self, connection, event):
        if event.eventtype() == "nowaway":
            self.away = True
        elif event.eventtype() == "unaway":
            self.away = False
            self.awaybecauseidle = False

    # These two functions set the away status
    def setaway(self, reason):
        for connection in self.irc.connections:
            connection.send_raw(_("AWAY: %s") % reason)

    def unaway(self):
        for connection in self.irc.connections:
            connection.send_raw(_("AWAY"))

    # This functions checks if X is idle. If yes, and if the user is not
    # already away, it puts the user in away status and remembers it. If not,
    # and if the user is away and he is away because he was idle, then it puts
    # the user back from away status. It also creates a timer to check if X is
    # idle at a later time. The best timeout is given by PyXSS, so we use it.
    def check_idle(self):
        info = self.tracker.check_idle()
        if info[0] == 'idle' and not self.idle:
            if not self.away:
                self.setaway(self.away_reason)
                self.awaybecauseidle = True
            self.idle = True
        elif info[0] == 'unidle' and self.idle:
            if self.awaybecauseidle:
                self.unaway()
                self.awaybecauseidle = False
            self.idle = False
        self.timer = threading.Timer(info[1]/1000, self.check_idle)
        self.timer.start()


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
                    self.notify(_("<b>Connection Sucessfull:</b>\n"
                                  "To irssi proxy on %(server)s:%(port)s") % {
                                    'server': server, 'port': port })
                else:
                    self.notify(_("<b>Connection Failed:</b>\nFailed to "
                                  "connect to %(server)s:%(port)s") % {
                                    'server': server, 'port': port })
            except irclib.ServerConnectionError, error:
                print error
                sys.exit(1)

    def start(self):
        if self.x_away:
            self.check_idle()

    def is_connected(self):
        connected = False
        for connection in self.irc.connections:
            if connection.connected:
                connected = True
        return connected

    def process(self, timeout=0):
        if self.is_connected():
            self.irc.process_once(timeout)
            return True
        return False

    def process_non_gui(self):
        while self.is_connected():
            #print "processing non GUI"
            self.irc.process_once(0.2)
        self.notify(_("Disconnected from server"))
        print _("Disconnected from server")
        self.quit()
        sys.exit(1)

    def quit(self):
        self.irc.disconnect_all()
        if self.timer:
            self.timer.cancel() # We kill the timer before exiting.
