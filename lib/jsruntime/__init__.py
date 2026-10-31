# -*- coding: utf-8 -*-
"""API publique de script.module.jsruntime.

    import jsruntime
    rt = jsruntime.find()            # ('deno', '/.../bin/deno') ou None
    rt = jsruntime.install(progress) # télécharge le moteur adapté à la machine
    jsruntime.install_with_dialog()  # même chose, avec barre de progression Kodi
"""
import xbmcaddon
import xbmcvfs

from .core import InstallError, detect_target, version_of  # noqa: F401
from . import core

ADDON_ID = 'script.module.jsruntime'


def profile_dir():
    return xbmcvfs.translatePath(xbmcaddon.Addon(ADDON_ID).getAddonInfo('profile'))


def find():
    return core.find(profile_dir())


def install(progress=None):
    return core.install(profile_dir(), progress)


def _target_label():
    target = detect_target()
    return '%s (%s)' % target if target else '?'


def install_with_dialog(heading=None):
    """Installe ou met à jour le moteur avec une barre de progression.

    Retourne (nom, chemin, version) ou None (échec ou annulation, déjà signalé).
    """
    import xbmc
    import xbmcgui
    addon = xbmcaddon.Addon(ADDON_ID)
    L = addon.getLocalizedString
    heading = heading or addon.getAddonInfo('name')
    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, L(32001))

    def progress(pct, text):
        dialog.update(pct, text)
        return dialog.iscanceled()
    dialog.update(0, '%s\n%s' % (L(32001), _target_label()))
    try:
        result = install(progress)
    except Exception as exc:  # InstallError ou imprévu : toujours affiché
        dialog.close()
        xbmc.log('[jsruntime] installation : %s' % exc, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(heading, L(32003) % exc)
        return None
    dialog.close()
    xbmc.log('[jsruntime] installé : %s %s (%s)' % (result[0], result[2], result[1]), xbmc.LOGINFO)
    xbmcgui.Dialog().notification(heading, L(32002) % result[2])
    return result
