# -*- coding: utf-8 -*-
"""Téléchargement et détection du moteur JavaScript.

Le binaire dépend de la machine et pèse 40 à 100 Mo : il n'est pas livré
dans le zip de l'addon mais téléchargé une fois dans
addon_data/script.module.jsruntime/bin/, que les mises à jour ne touchent pas.
  - Python 64 bits (ARM ou x86) : Deno, recommandé par yt-dlp
  - Python 32 bits ARM (userland 32 bits) : Node.js armv7l (Deno n'existe pas)
"""
import io
import os
import platform
import re
import stat
import struct
import subprocess
import zipfile

import requests

DENO_URL = 'https://github.com/denoland/deno/releases/latest/download/deno-%s-unknown-linux-gnu.zip'
NODE_INDEX = 'https://nodejs.org/dist/latest-v22.x/'


class InstallError(Exception):
    pass


def detect_target():
    """('deno', 'aarch64'|'x86_64') ou ('node', 'armv7l') ; None si non géré."""
    if platform.system() != 'Linux':
        return None
    machine = platform.machine().lower()
    bits = struct.calcsize('P') * 8
    if bits == 64 and machine in ('aarch64', 'arm64'):
        return 'deno', 'aarch64'
    if bits == 64 and machine in ('x86_64', 'amd64'):
        return 'deno', 'x86_64'
    if machine.startswith('arm') or machine in ('aarch64', 'arm64'):
        return 'node', 'armv7l'
    return None


def _download(url, progress, label, start, end):
    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise InstallError('téléchargement impossible : %s' % exc)
    total = int(resp.headers.get('Content-Length') or 0)
    buf = io.BytesIO()
    done = 0
    for chunk in resp.iter_content(256 * 1024):
        buf.write(chunk)
        done += len(chunk)
        if progress:
            pct = start + (end - start) * done / total if total else start
            if progress(int(pct), '%s  %.0f Mo' % (label, done / 1048576.0)):
                raise InstallError('annulé')
    return buf.getvalue()


def _write_exec(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.chmod(tmp, os.stat(tmp).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    os.replace(tmp, path)


def version_of(path):
    try:
        out = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallError('le moteur ne démarre pas sur cette machine : %s' % exc)
    if out.returncode != 0:
        raise InstallError('le moteur ne démarre pas sur cette machine : %s' % (out.stderr or '').strip()[:200])
    return (out.stdout or '').strip().splitlines()[0] if out.stdout else '?'


RUNTIMES = (('deno', 'deno'), ('node', 'node'))


def find(profile_dir):
    """(nom pour yt-dlp, chemin) du moteur installé, ou None."""
    for exe, key in RUNTIMES:
        path = os.path.join(profile_dir, 'bin', exe)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return key, path
    return None


def install(profile_dir, progress=None):
    """Installe le moteur adapté ; retourne (nom, chemin, version).

    progress(pourcentage, texte) -> True pour annuler.
    """
    target = detect_target()
    if target is None:
        raise InstallError('machine non prise en charge (%s, %s)' % (platform.system(), platform.machine()))
    kind, arch = target
    bindir = os.path.join(profile_dir, 'bin')
    os.makedirs(bindir, exist_ok=True)

    if kind == 'deno':
        data = _download(DENO_URL % arch, progress, 'Deno', 0, 90)
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                binary = zf.read('deno')
        except (zipfile.BadZipFile, KeyError) as exc:
            raise InstallError('archive Deno invalide : %s' % exc)
        path = os.path.join(bindir, 'deno')
    else:
        try:
            index = requests.get(NODE_INDEX, timeout=30).text
        except requests.RequestException as exc:
            raise InstallError('index Node.js inaccessible : %s' % exc)
        match = re.search(r'node-v[\d.]+-linux-armv7l\.tar\.xz', index)
        if not match:
            raise InstallError('archive Node.js armv7l introuvable')
        name = match.group(0)
        data = _download(NODE_INDEX + name, progress, 'Node.js', 0, 90)
        try:
            import tarfile
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as tf:
                member = tf.getmember('%s/bin/node' % name[:-len('.tar.xz')])
                binary = tf.extractfile(member).read()
        except (ImportError, KeyError, OSError) as exc:  # lzma absent, archive inattendue
            raise InstallError('extraction de Node.js impossible : %s' % exc)
        path = os.path.join(bindir, 'node')

    if progress:
        progress(95, 'Vérification…')
    _write_exec(path, binary)
    return kind, path, version_of(path)
