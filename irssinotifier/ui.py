# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: ui.py 53 2007-10-20 19:25:55Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/ui.py $
# $LastChangedDate: 2007-10-20 20:25:55 +0100 (Sat, 20 Oct 2007) $
#             $Rev: 53 $
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
from babel import Locale
import webbrowser

gobject.threads_init()

LANG_UPDATED = 0

( FRIENDS_NICK, FRIENDS_EDITABLE ) = range(2)
( LANG_LANGUAGE, LANG_LOCALE, LANG_INDEX) = range(3)
( PROXIES_HOST, PROXIES_PORT, PROXIES_NICK, PROXIES_EDITABLE ) = range(4)

class AboutGUI:
    "Class to define the 'About' gui."
    def __init__(self):
        gtk.about_dialog_set_url_hook(self.open_link)
        self.dialog = gtk.AboutDialog()
        self.dialog.set_name(_('Irssi Notifier'))
        self.dialog.set_version(irssinotifier.__version__)
        # TRANSLATOR: No need to translate copyright
        self.dialog.set_copyright(_('2007 © UfSoft.org'))
        self.dialog.set_comments(_('Irssi Real-Time Remote Visual '
                                   'Notifications'))
        self.dialog.set_license(irssinotifier.__license_text__)
        self.dialog.set_website(irssinotifier.__url__)
        self.dialog.set_website_label(_('Go To Development Site'))
        self.dialog.set_authors(['Pedro Algarvio <ufs@ufsoft.org>'])
        self.dialog.set_translator_credits('Pedro Algarvio <ufs@ufsoft.org>')
        img = gtk.gdk.pixbuf_new_from_file(
            os.path.join(os.path.dirname(__file__), 'data', 'irssi.png')
        )
        self.dialog.set_logo(img)
        self.dialog.set_icon(img)

        self.dialog.connect("response", lambda d, r: self.hide_about())

    def open_link(self, dialog, link, user_data=None):
        webbrowser.open(link, new=True, autoraise=True)

    def show_about(self, widget):
        self.dialog.show_all()

    def hide_about(self):
        self.dialog.hide_all()

class TrayApp:
    def __init__(self, options=(), cfgfile='~/.irssinotifier', notifier=None):
        self.options = options or {}
        self.cfgfile = cfgfile
        self.notifier = notifier
        self.config = ConfigParser.SafeConfigParser(options.__dict__)
        self.config.read(os.path.expanduser(self.cfgfile))
        # Read Glade File
        gladefile = os.path.join(os.path.dirname(__file__), 'data', 'glade',
                                 'prefs.glade')
        self.wTree = gtk.glade.XML(gladefile, 'PreferencesDialog',
                                   __glade_translator__)
        self.win = self.wTree.get_widget('PreferencesDialog')
        # Set Dialog Icon
        icon = gtk.gdk.pixbuf_new_from_file(
            os.path.join(os.path.dirname(__file__), 'data', 'irssi.png')
        )
        self.win.set_icon(icon)
        self.about = AboutGUI()

        # Add Our Hidden Reload Warning
        vbox = self.wTree.get_widget('OtherPrefsVbox')
        self.reload_warning = gtk.Label(_('<b><i>You need to reload '
                                          'application for changes to take '
                                          'effect.</i></b>'))
        self.reload_warning.set_use_markup(True)
        vbox.pack_end(self.reload_warning, False, False, padding=10)

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
                                               self.friends_treeview),
            "on_LanguageComboBox_changed": self.on_LanguageComboBox_changed,
            "on_BitlbeeCheckButton_toggled": self.on_BitlbeeCheckButton_toggled,
            "on_NotificationTimeOutSpinButton_value_changed":
                self._add_reload_info,
            "on_FallbackCharsetInput_key_press_event": self._add_reload_info,
            "on_ProxyPasswdInput_key_press_event": self._add_reload_info,
            "on_DebugModeCheckButton_toggled": self._add_reload_info,
            "on_RunGuiCheckButton_toggled": self._add_reload_info,
            "on_AwayReasonInput_key_press_event": self._add_reload_info,
            "on_AutoAwaySpinButton_value_changed": self._add_reload_info,

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
        self._populate_preferences()
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

        quit.connect_object('activate', self.exit_app, 'quit')
        about.connect_object('activate', self.about.show_about, 'about')
        prefs.connect_object('activate', self.show_prefs, 'prefs')
        about.show()
        prefs.show()
        quit.show()
        return menu

    def exit_app(self, widget=None):
        self.update_config_file()
        gobject.idle_add(self.notifier.quit)
        self.trayicon.set_visible(False)
        sys.exit(0)

    def pop_menu(self, statusicon, button, activate_time):
        self.menu.popup(None, None, gtk.status_icon_position_menu,
                        button, activate_time, statusicon)

    def main(self):
        #gtk.gdk.threads_init()
        self.notifier.start()
        gobject.timeout_add(500, self.notifier.process)
        gtk.main()

        def update_config_file(self):
        # Re-Init our config file
        self.config = ConfigParser.SafeConfigParser()
        friends = [
            entry[0] for entry in iter(self.friends_treeview.get_model())
        ]
        proxies = [
            tuple(entry) for entry in iter(self.proxies_treeview.get_model())
        ]
        # - Friends
        if not self.config.has_section('main'):
            self.config.add_section('main')
        self.config.set('main', 'friends', ' '.join(friends))
        # - Proxies
        proxy_entries = []
        for entry in proxies:
            proxy_entries.append(':'.join(entry[:-1]))
        self.config.set('main', 'proxies', ' '.join(proxy_entries))
        # - Notification Timeout
        timeout = self.wTree.get_widget('NotificationTimeOutSpinButton')
        self.config.set('main', 'timeout', "%d" % timeout.get_value())
        # - Irssi Proxy Passwd
        proxy_passwd = self.wTree.get_widget('ProxyPasswdInput')
        self.config.set('main', 'passwd', proxy_passwd.get_text())
        # - Debug Mode
        debug_chkbox = self.wTree.get_widget('DebugModeCheckButton')
        self.config.set('main', 'debug', "%s" % debug_chkbox.get_active())
        # - GUI
        gui_mode = self.wTree.get_widget('RunGuiCheckButton')
        self.config.set('main', 'gui', "%s" % gui_mode.get_active())
        # - Language
        langscb = self.wTree.get_widget('LanguageComboBox')
        lang_model = langscb.get_model()
        lang_text = langscb.get_active_text()
        for language, locale, index in lang_model:
            if language == lang_text:
                self.config.set('main', 'language', locale)
        # - Fallback Charset
        fbcharset = self.wTree.get_widget('FallbackCharsetInput')
        self.config.set('main', 'charset', fbcharset.get_text())
        # - Away-Reason
        away_reason = self.wTree.get_widget('AwayReasonInput')
        self.config.set('main', 'away_reason', away_reason.get_text())
        # - Away Timeout
        away_timeout = self.wTree.get_widget('AutoAwaySpinButton')
        self.config.set('main', 'x_away', "%d" % away_timeout.get_value())
        # - Bitlbee Notification
        bitlbee = self.wTree.get_widget('BitlbeeCheckButton')
        self.config.set('main', 'bitlbee', "%s" % bitlbee.get_active())
        # - Write Configs
        self.config.write(open(os.path.expanduser(self.cfgfile), 'w'))

    def delete_event(self, widget, *args):
        self.win.hide()
        return True

    def show_prefs(self, widget):
        self.win.show()

    def _get_available_locales(self):
        available_locales = []
        i18ndir = os.path.join(os.path.dirname(__file__), 'i18n')
        for entry in os.listdir(i18ndir):
            mo_path = os.path.join(i18ndir, entry, 'LC_MESSAGES',
                                   'irssinotifier.mo')
            if os.path.isfile(mo_path):
                if '_' in entry:
                    available_locales.append(tuple(entry.split('_')))
                else:
                    available_locales.append((entry, None))
        available_languages = []
        locl = Locale.parse(self.options.language)
        for locale, territory in available_locales:
            language = locl.languages[locale].capitalize()
            if territory:
                country = u'(%s)' % locl.territories[territory]
                value = ['%s_%s' % (locale, territory),
                         u'%s %s' % (language, country)]
            else:
                value = [locale, language]
            available_languages.append(value)

        return available_languages

    def _create_languages_model(self):
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_INT)
        for index, entry in enumerate(self._get_available_locales()):
            locale, language = entry
            iter = model.append()
            model.set(iter,
                      LANG_LANGUAGE, language,
                      LANG_LOCALE, locale,
                      LANG_INDEX, index)
        return model

    def _set_languages(self, combobox):
        model = self._create_languages_model()
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        for language, locale, index in model:
            if locale == self.options.language:
                combobox.set_active(index)

    def _create_friends_model(self):
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        for friend in self.options.friends:
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
        for entry in self.options.proxies:
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
        column = gtk.TreeViewColumn(_('Address'), renderer,
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

    def _populate_preferences(self):
        # Set Notification Timeout
        timeout = self.wTree.get_widget('NotificationTimeOutSpinButton')
        timeout.set_value(self.options.timeout)
        # Set Irssi Proxy Passwd
        proxy_passwd = self.wTree.get_widget('ProxyPasswdInput')
        proxy_passwd.set_visibility(False) # Hidden
        proxy_passwd.set_invisible_char('*')
        proxy_passwd.set_text(self.options.passwd)
        # Set Debug Mode
        debug_chkbox = self.wTree.get_widget('DebugModeCheckButton')
        debug_chkbox.set_active(self.options.debug)
        # Set Always in GUI Mode
        gui_mode = self.wTree.get_widget('RunGuiCheckButton')
        gui_mode.set_active(
            self.options.gui or self.config.getboolean('main', 'gui')
        )
        # Set Languages
        langscb = self.wTree.get_widget('LanguageComboBox')
        self._set_languages(langscb)

        # Set Fallback Charset
        fbcharset = self.wTree.get_widget('FallbackCharsetInput')
        fbcharset.set_text(self.options.charset or '')
        # Set Away-Reason
        away_reason = self.wTree.get_widget('AwayReasonInput')
        away_reason.set_text(self.options.away_reason)
        # Set Away Timeout
        away_timeout = self.wTree.get_widget('AutoAwaySpinButton')
        away_timeout.set_value(self.options.x_away)
        # Set Bitlebee Support Enabled
        bitlbee = self.wTree.get_widget('BitlbeeCheckButton')
#        bitlbee.set_active(not self.options.bitlbee)
#        self.on_BitlbeeCheckButton_toggled(bitlbee)
        bitlbee.set_active(self.options.bitlbee)
#        self.on_BitlbeeCheckButton_toggled(bitlbee)


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
                  PROXIES_HOST, _("ADDRESS_HERE"),
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

    def on_LanguageComboBox_changed(self, combobox):
        # User Will need to reload app
        global LANG_UPDATED
        if LANG_UPDATED > 0:
            self._add_reload_info()
        LANG_UPDATED += 1

    def on_BitlbeeCheckButton_toggled(self, checkbox):
        if checkbox.get_active():
            self.wTree.get_widget('AwayReasonHbox').show()
            self.wTree.get_widget('AutoAwayHbox').show()
        else:
            self.wTree.get_widget('AwayReasonHbox').hide()
            self.wTree.get_widget('AutoAwayHbox').hide()

        self._add_reload_info()

    def _add_reload_info(self, *args):
        if not self.reload_warning.props.visible:
            self.reload_warning.show()

    def on_OkButton_clicked(self, button):
        friends = [
            entry[0] for entry in iter(self.friends_treeview.get_model())
        ]
        proxies = [
            tuple(entry) for entry in iter(self.proxies_treeview.get_model())
        ]
        # Handle Notifier
        # - Update Friends
        self.notifier.friends = friends
        # - Update Proxies
        self.notifier.proxies = proxies
        self.delete_event(button)
        return True

    def on_CancelButton_clicked(self, button):
        self.delete_event(button)


def run_tray_app():
    tapp = TrayApp()
    tapp.main()

