# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: ui.py 7 2007-07-13 09:58:26Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/ui.py $
# $LastChangedDate: 2007-07-13 10:58:26 +0100 (Fri, 13 Jul 2007) $
#             $Rev: 7 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

# http://www.pygtk.org/pygtk2tutorial/ch-MenuWidget.html#sec-ManualMenuCreation
# http://www.pygtk.org/docs/pygtk/class-gtkstatusicon.html

import os
import sys
import gtk
import ConfigParser


class TrayApp:
    def __init__(self):
        self.config = self.read_config()
        print self.config
        self.proxies_box = Proxies()
        self.trayicon = self.create_tray_icon()
        self.menu = self.create_menu()

    def read_config(self, configfile='~/.irssinotifier'):
        cfgfile = os.path.expanduser(configfile)
        if os.path.exists(cfgfile):
            config = ConfigParser.SafeConfigParser()
            config.read(cfgfile)
            if config.has_section('main'):
                opts = {}
                for opt in (
                    'nick', 'passwd', 'name', 'proxies', 'friends', 'timeout'):
                    try:
                        if opt in ('proxies', 'friends'):
                            opts[opt] = config.get('main', opt).split()
                        elif opt == 'timeout':
                            try:
                                opts[opt] = config.getint('main', 'timeout')
                            except ValueError:
                                opts[opt] = int(config.getfloat('main', 'timeout'))
                        else:
                            opts[opt] = config.get('main', opt)
                    except ConfigParser.NoOptionError:
                        continue
            return opts

    def create_tray_icon(self):
        img = os.path.join(os.path.dirname(__file__), 'irssi.xpm')
        trayicon = gtk.status_icon_new_from_file(img)
        trayicon.connect('popup-menu', self.pop_menu)
        trayicon.set_tooltip('Irssi Notifier')
        trayicon.set_visible(True)
        return trayicon

    def create_menu(self):
        menu = gtk.Menu()
        connect = gtk.MenuItem("Connect")
        disconnect = gtk.MenuItem("Disconnect")
        quit = gtk.MenuItem("Quit")
        separator = gtk.HSeparator()
        proxies = gtk.MenuItem("Configure Proxies")
        menu.append(proxies)
        menu.append(separator)
        menu.append(connect)
        menu.append(disconnect)
        menu.append(separator)
        menu.append(quit)

        quit.connect_object('activate', self.exit, 'quit')
        proxies.connect_object('activate', self.proxies_box.main, 'proxies')
        proxies.show()
        connect.show()
        disconnect.show()
        separator.show()
        quit.show()
        return menu

    def exit(self, status_icon):
        self.trayicon.destroy()
        sys.exit(0)

    def pop_menu(self, statusicon, button, activate_time):
        self.menu.popup(None, None, gtk.status_icon_position_menu,
                        button, activate_time, statusicon)

    def main(self):
        gtk.main()


class Proxies:
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        # You should always remember to connect the delete_event signal
        # to the main window. This is very important for proper intuitive
        # behavior
        self.window.connect("delete_event", self.delete_event)
        self.window.set_border_width(10)
        listbox = gtk.VBox(False, 0)
        listbox_label = gtk.Label("Proxies")
        listbox_label.set_alignment(0, 0)
        listbox.pack_start(listbox_label, False, False, 0)
        listbox_label.show()
        buttonsbox = gtk.HBox(False, 0)
        close_button = gtk.Button("Close")
        close_button.connect("clicked", lambda w: gtk.main_quit())
        buttonsbox.pack_start(close_button, True, False, 0)
        listbox.pack_start(buttonsbox, False, False, 0)
        self.window.add(listbox)
        close_button.show()
        listbox.show()
        buttonsbox.show()

    def delete_event(self, widget, event, data=None):
        self.window.hide()
        return False

    def main(self):
        self.window.show()
        gtk.main()

def run_tray_app():
    tapp = TrayApp()
    tapp.main()