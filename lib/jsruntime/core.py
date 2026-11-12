# -*- coding: utf-8 -*-
"""Téléchargement et détection du moteur JavaScript.

Le binaire dépend de la machine et pèse 40 à 100 Mo : il n'est pas livré
dans le zip de l'addon mais téléchargé une fois dans
addon_data/script.module.jsruntime/bin/, que les mises à jour ne touchent pas.
  - Python 64 bits (ARM ou x86) : Deno, recommandé par yt-dlp
  - Python 32 bits ARM (userland 32 bits) : Node.js armv7l (Deno n'existe pas)
"""
import hashlib
import os
import platform
import re
import shutil
import stat
import struct
import subprocess
import tempfile
import zipfile

import requests

DENO_URL = 'https://github.com/denoland/deno/releases/latest/download/deno-%s-unknown-linux-gnu.zip'
NODE_INDEX = 'https://nodejs.org/dist/latest-v22.x/'


# La dernière installation a-t-elle été contrôlée par sa somme SHA-256 ?
LAST_VERIFIED = False


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


def _download(url, dest, progress, label, start, end):
    """Télécharge url dans le fichier dest, au fil de l'eau (l'archive pèse
    40 à 100 Mo : elle ne passe plus par la mémoire). Retourne son SHA-256."""
    digest = hashlib.sha256()
    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        total = int(resp.headers.get('Content-Length') or 0)
        done = 0
        with open(dest, 'wb') as fh:
            for chunk in resp.iter_content(256 * 1024):
                fh.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                if progress:
                    pct = start + (end - start) * done / total if total else start
                    if progress(int(pct), '%s  %.0f Mo' % (label, done / 1048576.0)):
                        raise InstallError('annulé')
    except requests.RequestException as exc:
        raise InstallError('téléchargement impossible : %s' % exc)
    except OSError as exc:
        raise InstallError('écriture impossible (espace disque ?) : %s' % exc)
    return digest.hexdigest()


def _published_sha256(url, filename):
    """Somme SHA-256 publiée pour filename (format « somme  nom » par ligne).

    None si la liste est injoignable : l'installation continue alors sans
    contrôle, comme avant la 1.0.3. Une somme trouvée et différente de celle
    du fichier téléchargé arrête toujours l'installation."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    for line in resp.text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip('*') == filename \
                and re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]):
            return parts[0].lower()
    return None


def _check_sha256(expected, actual, name):
    """True si la somme a été vérifiée, False si aucune n'était disponible."""
    if expected is None:
        return False
    if expected != actual:
        raise InstallError('fichier %s altéré ou incomplet (somme SHA-256 différente de celle '
                           'publiée) : relance l\'installation' % name)
    return True


def _make_exec(path):
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _clean_leftovers(bindir):
    """Retire les fichiers temporaires d'une installation interrompue (Kodi
    arrêté ou box débranchée en plein téléchargement) : ils pèsent jusqu'à
    une centaine de Mo et ne servent plus à rien."""
    try:
        names = os.listdir(bindir)
    except OSError:
        return
    for name in names:
        if name.endswith(('.tmp', '.new')):
            try:
                os.remove(os.path.join(bindir, name))
            except OSError:
                pass


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

    Le nouveau moteur est écrit à côté de l'ancien, lancé une fois, et ne le
    remplace que s'il démarre : une mise à jour ratée (binaire incompatible
    avec la machine, disque plein) laisse le moteur précédent en place.
    """
    global LAST_VERIFIED
    target = detect_target()
    if target is None:
        raise InstallError('machine non prise en charge (%s, %s)' % (platform.system(), platform.machine()))
    kind, arch = target
    bindir = os.path.join(profile_dir, 'bin')
    try:
        os.makedirs(bindir, exist_ok=True)
        _clean_leftovers(bindir)
        fd, archive = tempfile.mkstemp(prefix='download-', suffix='.tmp', dir=bindir)
        os.close(fd)
    except OSError as exc:
        raise InstallError('dossier d\'installation inaccessible : %s' % exc)

    path = os.path.join(bindir, 'deno' if kind == 'deno' else 'node')
    candidate = path + '.new'
    try:
        if kind == 'deno':
            name = 'deno-%s-unknown-linux-gnu.zip' % arch
            expected = _published_sha256(DENO_URL % arch + '.sha256sum', name)
            actual = _download(DENO_URL % arch, archive, progress, 'Deno', 0, 90)
            checked = _check_sha256(expected, actual, name)
            try:
                # Extraction au fil de l'eau : le binaire (plus de 100 Mo)
                # ne passe pas par la mémoire.
                with zipfile.ZipFile(archive) as zf, zf.open('deno') as src, open(candidate, 'wb') as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
            except (zipfile.BadZipFile, KeyError, OSError) as exc:
                raise InstallError('archive Deno invalide ou disque plein : %s' % exc)
        else:
            try:
                index = requests.get(NODE_INDEX, timeout=30).text
            except requests.RequestException as exc:
                raise InstallError('index Node.js inaccessible : %s' % exc)
            match = re.search(r'node-v[\d.]+-linux-armv7l\.tar\.xz', index)
            if not match:
                raise InstallError('archive Node.js armv7l introuvable')
            name = match.group(0)
            expected = _published_sha256(NODE_INDEX + 'SHASUMS256.txt', name)
            actual = _download(NODE_INDEX + name, archive, progress, 'Node.js', 0, 90)
            checked = _check_sha256(expected, actual, name)
            try:
                import tarfile
                with tarfile.open(archive, mode='r:xz') as tf:
                    member = tf.getmember('%s/bin/node' % name[:-len('.tar.xz')])
                    with tf.extractfile(member) as src, open(candidate, 'wb') as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)
            except InstallError:
                raise
            except Exception as exc:  # lzma absent, archive tronquée ou inattendue, disque plein
                raise InstallError('extraction de Node.js impossible : %s' % exc)

        if progress:
            progress(95, 'Vérification…')
        try:
            _make_exec(candidate)
        except OSError as exc:
            raise InstallError('écriture du moteur impossible : %s' % exc)
        # Le nouveau moteur doit démarrer AVANT de remplacer l'ancien.
        version = version_of(candidate)
        try:
            os.replace(candidate, path)
        except OSError as exc:
            raise InstallError('mise en place du moteur impossible : %s' % exc)
    finally:
        for leftover in (archive, candidate):
            try:
                os.remove(leftover)
            except OSError:
                pass
    LAST_VERIFIED = checked
    return kind, path, version
