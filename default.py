# -*- coding: utf-8 -*-
"""Lancé depuis Programmes, Extensions ou RunScript(script.module.jsruntime) :
installe ou met à jour le moteur JavaScript."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

import xbmc  # noqa: E402
import xbmcgui  # noqa: E402

xbmc.log('[jsruntime] lancement de l\'installation', xbmc.LOGINFO)
try:
    import jsruntime  # noqa: E402
    jsruntime.install_with_dialog()
except Exception as exc:  # toute erreur doit être visible, pas seulement dans le journal
    import traceback
    xbmc.log('[jsruntime] échec : %s\n%s' % (exc, traceback.format_exc()), xbmc.LOGERROR)
    xbmcgui.Dialog().ok('Moteur JavaScript', 'Erreur : %s' % exc)
