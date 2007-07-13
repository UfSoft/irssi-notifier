#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: translation.py 8 2007-07-13 14:23:18Z s0undt3ch $
# =============================================================================
#             $URL: http://irssinotifier.ufsoft.org/svn/trunk/irssinotifier/translation.py $
# $LastChangedDate: 2007-07-13 15:23:18 +0100 (Fri, 13 Jul 2007) $
#             $Rev: 8 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import os
import gettext
import __builtin__

def set_lang(lang, codeset='utf-8'):
    if not isinstance(lang, list):
        lang = [lang]

    locale_dir = os.path.join(os.path.dirname(__file__), 'i18n')

    try:
        translator = gettext.translation('irssinotifier',
                                         locale_dir,
                                         languages=lang,
                                         codeset=codeset)
    except IOError, ioe:
        print 'Language not supportted: %r' % ioe
        print 'Fallback to english'
        translator = gettext.translation('irssinotifier',
                                         locale_dir,
                                         languages=['en'],
                                         codeset=codeset)
    # install _ into builtins
    __builtin__.__dict__['_'] = translator.ugettext