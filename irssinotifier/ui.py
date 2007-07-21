# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: ui.py 14 2007-07-21 11:24:12Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/ui.py $
# $LastChangedDate: 2007-07-21 12:24:12 +0100 (Sat, 21 Jul 2007) $
#             $Rev: 14 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import os
import sys
import gtk
import gtk.glade
import gobject
import ConfigParser
import irssinotifier

( FRIENDS_NICK, FRIENDS_EDITABLE ) = range(2)
( PROXIES_HOST, PROXIES_PORT, PROXIES_NICK, PROXIES_EDITABLE ) = range(4)

class AboutGUI:
    def __init__(self):
        self.dialog = gtk.AboutDialog()
        self.dialog.set_name(_('Irssi Notifier'))
        self.dialog.set_version(irssinotifier.__version__)
        # TRANSLATOR: No need to translate copyright
        self.dialog.set_copyright(_('2007 © UfSoft.org'))
        self.dialog.set_comments(_('Irssi Real-Time Remote Visual '
                                   'Notifications'))
        license = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               'LICENSE')
        self.dialog.set_license(open(license).read())
        self.dialog.set_website(irssinotifier.__url__)
        self.dialog.set_website_label(_('Development Site'))
        self.dialog.set_authors(['Pedro Algarvio <ufs@ufsoft.org>'])
        self.dialog.set_translator_credits('Pedro Algarvio <ufs@ufsoft.org>')
        img = gtk.gdk.pixbuf_new_from_file(
            os.path.join(os.path.dirname(__file__), 'data', 'irssi.png')
        )
        self.dialog.set_logo(img)
        self.dialog.set_icon(img)

        self.dialog.connect("response", lambda d, r: self.hide_about())

    def show_about(self, widget):
        self.dialog.show_all()

    def hide_about(self):
        self.dialog.hide_all()

class TrayApp:
    def __init__(self, config={}, cfgfile='~/.irssinotifier', notifier=None):
        self.config = config
        self.cfgfile = cfgfile
        self.notifier = notifier
        # Read Glade File
        gladefile = os.path.join(os.path.dirname(__file__), 'data', 'glade',
                                 'prefs.glade')
        self.wTree = gtk.glade.XML(gladefile, 'PreferencesDialog')
        self.win = self.wTree.get_widget('PreferencesDialog')
        # Set Dialog Icon
        icon = gtk.gdk.pixbuf_new_from_file(
            os.path.join(os.path.dirname(__file__), 'data', 'irssi.png')
        )
        self.win.set_icon(icon)
        self.about = AboutGUI()
        self.friends_treeview = self.wTree.get_widget('FriendsTreeView')
        self.proxies_treeview = self.wTree.get_widget('ProxiesTreeView')
        events = {
            "on_cancel_clicked": self.delete_event,
            "on_OkButton_clicked": self.on_OkButton_clicked,
            "on_CancelButton_clicked": self.on_CancelButton_clicked,
            "on_AddProxiesButton_clicked": (self.on_AddProxiesButton_clicked,
                                            self.proxies_treeview),
            "on_RemoveProxiesButton_clicked": (self.on_RemoveProxiesButton_clicked,
                                               self.proxies_treeview),
            "on_AddFriendsButton_clicked": (self.on_AddFriendsButton_clicked,
                                            self.friends_treeview),
            "on_RemoveFriendsButton_clicked": (self.on_RemoveFriendsButton_clicked,
                                               self.friends_treeview)
        }
        self.wTree.signal_autoconnect(events)
        # Friends Tab
        friends_model = self._create_friends_model()
        self.friends_treeview.set_model(friends_model)
        self._create_friends_columns(self.friends_treeview)
        # Proxies Tab
        proxies_model = self._create_proxies_model()
        self.proxies_treeview.set_model(proxies_model)
        self._create_proxies_columns(self.proxies_treeview)
        self.trayicon = self.create_tray_icon()
        self.menu = self.create_menu()

    def create_tray_icon(self):
        trayicon = gtk.StatusIcon()
        img = os.path.join(os.path.dirname(__file__), 'data', 'irssi.png')
        trayicon.set_from_file(img)
        trayicon.connect('popup-menu', self.pop_menu)
        trayicon.set_tooltip(_('Irssi Notifier'))
        trayicon.set_visible(True)
        return trayicon

    def create_menu(self):
        menu = gtk.Menu()
        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        menu.append(about)
        menu.append(prefs)
        menu.append(quit)

        quit.connect_object('activate', self.exit, 'quit')
        about.connect_object('activate', self.about.show_about, 'about')
        prefs.connect_object('activate', self.show_prefs, 'prefs')
        about.show()
        prefs.show()
        quit.show()
        return menu

    def exit(self, widget):
        self.notifier.quit()
        self.trayicon.set_visible(False)
        sys.exit(0)

    def pop_menu(self, statusicon, button, activate_time):
        self.menu.popup(None, None, gtk.status_icon_position_menu,
                        button, activate_time, statusicon)

    def main(self):
        gtk.main()
        self.notifier.start()

    def delete_event(self, widget, *args):
        self.win.hide_all()
        return True

    def show_prefs(self, widget):
        self.win.show_all()

    def _create_friends_model(self):
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        for friend in self.config.friends:
            iter = model.append()
            model.set(iter,
                      FRIENDS_NICK, friend,
                      FRIENDS_EDITABLE, True)
        return model

    def _create_friends_columns(self, friends_tree_view):
        model = friends_tree_view.get_model()
        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.on_cell_edited, model)
        renderer.set_data("column", FRIENDS_NICK)
        column = gtk.TreeViewColumn(_('Nick'), renderer, text=FRIENDS_NICK,
                                    editable=FRIENDS_EDITABLE)
        friends_tree_view.append_column(column)

    def _create_proxies_model(self):
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        for entry in self.config.proxies:
            host, port, nick = entry.split(':')
            iter = model.append()
            model.set(iter,
                      PROXIES_HOST, host,
                      PROXIES_PORT, port,
                      PROXIES_NICK, nick,
                      PROXIES_EDITABLE, True)
        return model

    def _create_proxies_columns(self, proxies_tree_view):
        model = proxies_tree_view.get_model()
        # Host
        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.on_cell_edited, model)
        renderer.set_data("column", PROXIES_HOST)
        column = gtk.TreeViewColumn(_('Host'), renderer,
                                    text=PROXIES_HOST,
                                    editable=PROXIES_EDITABLE)
        proxies_tree_view.append_column(column)

        # Port
        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.on_cell_edited, model)
        renderer.set_data("column", PROXIES_PORT)
        column = gtk.TreeViewColumn(_('Port'), renderer,
                                    text=PROXIES_PORT,
                                    editable=PROXIES_EDITABLE)
        proxies_tree_view.append_column(column)

        # Nick
        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.on_cell_edited, model)
        renderer.set_data("column", PROXIES_NICK)
        column = gtk.TreeViewColumn(_('Nick'), renderer,
                                    text=PROXIES_NICK,
                                    editable=PROXIES_EDITABLE)
        proxies_tree_view.append_column(column)

    def on_cell_edited(self, cell, path_string, new_text, model):
        #print "on cell edit called"
        #print "cell", cell, "path_string", path_string, "new_text", new_text
        iter = model.get_iter_from_string(path_string)
        path = model.get_path(iter)[0]
        column = cell.get_data("column")
        model.set(iter, column, new_text)

    def on_AddProxiesButton_clicked(self, button, treeview):
        model = treeview.get_model()
        iter = model.append()
        model.set(iter,
                  PROXIES_HOST, _("HOST_HERE"),
                  PROXIES_PORT, _("PORT_HERE"),
                  PROXIES_NICK, _("NICK_HERE"),
                  PROXIES_EDITABLE, True)

    def on_RemoveProxiesButton_clicked(self, button, treeview):
        self._remove_item_from_treeview(treeview)

    def on_AddFriendsButton_clicked(self, button, treeview):
        model = treeview.get_model()
        iter = model.append()
        model.set(iter,
                  FRIENDS_NICK, _("NICK_HERE"),
                  FRIENDS_EDITABLE, True)

    def on_RemoveFriendsButton_clicked(self, button, treeview):
        self._remove_item_from_treeview(treeview)

    def _remove_item_from_treeview(self, treeview):
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            path = model.get_path(iter)[0]
            model.remove(iter)

    def on_OkButton_clicked(self, button):
        friends = [entry[0] for entry in iter(self.friends_treeview.get_model())]
        proxies = [tuple(entry) for entry in iter(self.proxies_treeview.get_model())]
        # Handle Notifier
        # - Update Friends
        self.notifier.friends = friends
        self.notifier.proxies = proxies

        #Handle Config File
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.expanduser(self.cfgfile))
        # - Friends
        if not config.has_section('main'):
            config.add_section('main')
        config.set('main', 'friends', ' '.join(friends))
        # - Proxies
        proxy_entries = []
        for entry in proxies:
            proxy_entries.append(':'.join(entry[:-1]))
        config.set('main', 'proxies', ' '.join(proxy_entries))

        # - Write Configs
        config.write(open(os.path.expanduser(self.cfgfile), 'w'))
        self.delete_event(button)
        return True

    def on_CancelButton_clicked(self, button):
        self.delete_event(button)

def run_tray_app():
    tapp = TrayApp()
    tapp.main()