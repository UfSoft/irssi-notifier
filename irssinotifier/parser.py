# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: parser.py 8 2007-07-13 14:23:18Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/parser.py $
# $LastChangedDate: 2007-07-13 15:23:18 +0100 (Fri, 13 Jul 2007) $
#             $Rev: 8 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import os
import sys
from optparse import OptionParser
import ConfigParser
from irssinotifier import __version__ as VERSION
from irssinotifier.translation import *

class IrssiProxyNotifierStartup:
    def __init__(self):
        parser = OptionParser(
            usage = "%prog [options]",
            version = "%prog " + VERSION
        )
        parser.description = "%prog is intended to give you a visual, non " + \
        "obtrusive notification of messages addressed to you or mentioned " + \
        "to you"
        parser.add_option(
            '--config', '-C',
            dest = 'configfile',
            metavar = 'PATH_TO_FILE',
            help = "Provide an alternate configuration file. "
            "Default: '~/.irssinotifier'"
        )
        parser.add_option(
            '--nick', '-n',
            dest = 'nick',
            default = '',
            help = "Global nickname to pass to irssi-proxy. Use it if your "
            "nick is the same for all networks. Default: '%default'"
        )
        parser.add_option(
            '--passwd', '-p',
            dest = 'passwd',
            help = "Irssi proxy password"
        )
        parser.add_option(
            '--name', '-N',
            dest = 'name',
            default = '',
            help = "Your Name. Default: '%default'"
        )
        parser.add_option(
            '--proxies', '-P',
            action = 'append',
            dest = 'proxies',
            default = [],
            metavar = 'ADDRESS:PORT[:NICK]',
            help = "Pass an irssi-proxy address:port to be notified of. "
            "Repeat the argument to add more servers. You can optionally "
            "pass the nick for that network if your not using the global "
            "one and your nicks differ from network to netowrk. Default: %default"
        )
        parser.add_option(
            '--friend', '-F',
            action = 'append',
            dest = 'friends',
            metavar = 'FRIEND',
            default = [],
            help = "List of friends to be notified of parts, joins and quits. "
            "One friend per argument call. Default: %default"
        )
        parser.add_option(
            '--timeout', '-T',
            type = 'int',
            dest = 'timeout',
            metavar = 'SECONDS',
            default = 5,
            help = "Notification pop-up timeout (in seconds). Default: %default"
        )
        # These options allow the user to be automatically put in away mode
        # when X has been idle for some time.
        parser.add_option(
            '--x-away', '-X',
            type = int,
            dest = 'x_away',
            metavar = 'SECONDS',
            default = 0,
            help = "Enable auto-away according to X idle time (0 to disable). "
            "Default: %default"
        )
        parser.add_option(
            '--x-away-reason', '-R',
            dest = 'away_reason',
            default = 'inactivity',
            help = "The away reason to use in case of X inactivity. Default:"
            "'%default' "
        )
        # If this option is set, the server is known to be of bitlbee type,
        # and we will check &bitlbee to see if friends come online.
        parser.add_option(
            '--bitlbee', '-b',
            action = 'store_true',
            default = False,
            dest = 'bitlbee',
            help = "Enable notifications of away/joins/quits on a bitlbee server"
        )
        # This option is the charset to fallback to when text received is not
        # in UTF-8.
        parser.add_option(
            '--fallback-charset', '-c',
            dest = 'charset',
            default = None,
            help = "The charset to fallback to when messages received are not"
                   "in UTF-8. Default: '%default' "
        )
        parser.add_option(
            '--language', '-l',
            dest='language',
            default='en',
            help="Use the specified language translation. Default: %default"
        )
        parser.add_option(
            '--write-configs', '-W',
            action = 'store_true',
            default = False,
            dest = 'write_configs',
            help = "Write the options to the configuration file "
            "'~/.irssinotifier'"
        )
        parser.add_option(
            '--debug',
            action='store_true',
            default=False,
            dest='debug',
            help='Output IRCLib debug messages(extremely verbose)')
        self.parser = parser

    def parse_args(self, configfile='~/.irssinotifier'):
        """First parse the user's configuration file for options, if available
        make them the defaults for the parser
        """
        cfgfile = os.path.expanduser(configfile)
        if os.path.exists(cfgfile):
            config = ConfigParser.SafeConfigParser()
            config.read(cfgfile)
            if config.has_section('main'):
                opts = {}
                for opt in (
                    'nick', 'passwd', 'name', 'proxies', 'friends', 'timeout',
                    'x_away', 'away_reason', 'charset', 'bitlbee'):
                    try:
                        if opt in ('proxies', 'friends'):
                            opts[opt] = config.get('main', opt).split()
                        elif opt in ('timeout', 'x_away'):
                            try:
                                opts[opt] = config.getint('main', opt)
                            except ValueError:
                                opts[opt] = int(config.getfloat('main',
                                                                'timeout'))
                        elif opt == 'bitlbee':
                            opts[opt] = config.getboolean('main', 'bitlbee')
                        else:
                            opts[opt] = config.get('main', opt)
                    except ConfigParser.NoOptionError:
                        continue
                if opts:
                    self.parser.set_defaults(**opts)
        return self.parser.parse_args()

    def run(self):
        (options, args) = self.parse_args()
        if options.configfile:
            # We must re-parse
            (options, args) = self.parse_args(configfile=options.configfile)
        else:
            options.configfile = '~/.irssinotifier'

        if options.debug:
            import irclib
            irclib.DEBUG = True

        if options.charset:
            charset = options.charset
        else:
            charset = 'utf-8'

        proxies = []
        for proxy in options.proxies:
            t = proxy.split(':')
            if len(t) == 3:
                # Also passed User
                entry = (t[0], int(t[1]), t[2])
                if entry not in proxies:
                    proxies.append(entry)
            elif len(t) == 2:
                # No user passed
                if not options.nick:
                    self.parser.error("You must provide your nick."
                        "Either pass it on --proxies or on --nick"
                    )
                entry = (t[0], int(t[1]), options.nick)
                if entry not in proxies:
                    proxies.append(entry)
            else:
                self.parser.error("Bad arguments passed to --proxies %r" % proxy)
        friends = []
        for friend in options.friends:
            if friend not in friends:
                friends.append(friend)

        timeout = options.timeout * 1000
        # We need an ms value.
        x_away = options.x_away * 1000

        if options.write_configs:
            print "Writing configuration to %r ..." % options.configfile
            cfgfile = os.path.expanduser(options.configfile)
            cfgfile = open(cfgfile, 'w')
            config = ConfigParser.SafeConfigParser()
            config.add_section('main')
            print 'passwd\t...',
            if options.passwd:
                print 'OK'
                config.set('main', 'passwd', options.passwd)
            else:
                print 'no %r option set!' % 'passwd'
            print 'proxies\t...',
            local_proxies = []
            for host, port, user in proxies:
                entry = '%s:%s:%s' % ( host, port, user )
                if entry not in local_proxies:
                    local_proxies.append(entry)
            if local_proxies:
                config.set('main', 'proxies', ' '.join(local_proxies))
                print 'OK'
            else:
                print 'no %r option set!' % 'proxies'
            print 'timeout\t...',
            if options.timeout:
                config.set('main', 'timeout', str(options.timeout))
                print 'OK'
            else:
                print 'no %r option set!' % 'timeout'
            print 'x-away\t...',
            if options.x_away:
                config.set('main', 'x_away', str(options.x_away))
                print 'OK'
            else:
                print 'no %r option set!' % 'x-away'
            print 'reason\t...',
            if options.away_reason:
                config.set('main', 'away_reason', options.away_reason)
                print 'OK'
            else:
                print 'no %r option set!' % 'x-away-reason'
            if options.charset:
                config.set('main', 'charset', options.charset)
                print 'OK'
            else:
                print 'no %r option set!' % 'fallback-charset'
            print 'friends\t...',
            if friends:
                config.set('main', 'friends', ' '.join(friends))
                print 'OK'
            else:
                print 'no %r option set!' % 'friends'
            print 'bitlbee\t...',
            if options.bitlbee:
                config.set('main', 'bitlbee', str(options.bitlbee))
                print 'OK'
            else:
                print 'no %r option set!' % 'bitlbee'
            config.write(cfgfile)
            print "Done!"
            sys.exit(1)

        if not options.passwd:
            self.parser.error("You must provide the irssi-proxy password")

        if not options.proxies:
            self.parser.error(
                "You must pass at least one irssi-proxy addr:port"
            )

        set_lang(options.language, charset)
        # Late import so translations are not ignored
        from irssinotifier.notifier import IrssiProxyNotifier

        notifier = IrssiProxyNotifier(
            options.passwd,
            name=options.name,
            timeout=timeout,
            proxies=proxies,
            friends=friends,
            charset=options.charset,
            x_away=x_away,
            away_reason=options.away_reason,
            bitlbee=options.bitlbee
        )
        notifier.connect()
        if options.debug:
            try:
                notifier.start()
            except KeyboardInterrupt:
                notifier.quit()
                sys.exit(1)
        else:
            try:
                notifier.start()
            finally:
                notifier.quit()
                sys.exit(1)

def main():
    ipn = IrssiProxyNotifierStartup()
    ipn.run()
