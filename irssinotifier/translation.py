#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: translation.py 19 2007-07-24 18:16:48Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/translation.py $
# $LastChangedDate: 2007-07-24 19:16:48 +0100 (Tue, 24 Jul 2007) $
#             $Rev: 19 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import os
import gettext
import locale
import __builtin__

def set_lang(lang, codeset='utf-8', gui=False):
    if not isinstance(lang, list):
        lang = [lang]

    locale_dir = os.path.join(os.path.dirname(__file__), 'i18n')
    domain = 'irssinotifier'

    gettext.bindtextdomain(domain, locale_dir)
    gettext.textdomain(domain)
    locale.bindtextdomain(domain, locale_dir)
    locale.textdomain(domain)
    if gui:
        import gtk.glade
        gtk.glade.bindtextdomain(domain)
        gtk.glade.textdomain(domain)

    try:
        translator = gettext.translation(domain,
                                         locale_dir,
                                         languages=lang,
                                         codeset=codeset)

    except IOError, ioe:
        lang = ['en']
        print 'Language not supportted: %r' % ioe
        print 'Fallback to english'
        translator = gettext.translation(domain,
                                         locale_dir,
                                         languages=lang,
                                         codeset=codeset)

    if lang[0] != 'en' and gui:
        # We only need to do this because the Glade GUI reads info
        # from the environment
        new_locale = '.'.join([lang[0], locale.getdefaultlocale()[1]])
        try:
            os.environ['LC_ALL'] = new_locale
            locale.setlocale(locale.LC_ALL,'')
        except locale.Error:
            import sys
            print "Locale %r is not supported" % new_locale
            print "Please update/generate your system locales with the new"
            print "locale you want to use"
            sys.exit(1)

    __builtin__._ = translator.ugettext
    __builtin__.__glade_translator__ = locale.textdomain(domain)
    # Late import to make use of locale set
    from irssinotifier import notifier, ui

