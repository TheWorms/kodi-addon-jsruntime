**Français** · [English](readme.en.md)

# Moteur JavaScript pour Kodi

<!-- version:auto -->
**Version : 1.0.2**
<!-- /version:auto -->

Module Kodi qui installe un **moteur JavaScript** (Deno ou Node.js) pour les addons qui en ont
besoin. Il sert notamment à [Wtube](https://github.com/TheWorms/kodi-addon-youtube) : yt-dlp
doit exécuter les défis JavaScript de YouTube, faute de quoi les vidéos sont bloquées.

Le binaire (40 à 100 Mo) n'est **pas livré dans le zip** : il est téléchargé une seule fois,
dans le bon format pour la machine, puis conservé dans
`addon_data/script.module.jsruntime/bin/`, que les mises à jour ne touchent pas.

| Système | Moteur téléchargé |
|---------|-------------------|
| Linux 64 bits ARM (aarch64) — CoreELEC / LibreELEC 64 bits | Deno |
| Linux 64 bits x86 | Deno |
| Linux ARM 32 bits (userland armv7) | Node.js 22 (Deno n'existe pas en 32 bits) |

## Installation

**Recommandé — dépôt TheWorms** (mises à jour automatiques). Le module est installé
automatiquement avec les addons qui en dépendent.

Télécharge le dépôt en cliquant **[ICI](https://raw.githubusercontent.com/TheWorms/kodi-repo/main/zips/repository.theworms/repository.theworms.zip)**, puis dans Kodi :

1. **Add-ons** → **Installer depuis un fichier zip** → sélectionne le zip téléchargé
   *(si Kodi bloque, active **Sources inconnues** dans Système → Add-ons)*
2. **Installer depuis un dépôt** → **TheWorms Repository** → **Programmes** → **Moteur JavaScript**

Ensuite, lance **Programmes → Moteur JavaScript** : une barre de progression suit le
téléchargement, puis une notification indique la version installée. Relance-le pour mettre
le moteur à jour.

**Installation manuelle (alternative) :** télécharge le zip depuis la page [Releases](../../releases), puis **Add-ons** → **Installer depuis un fichier zip**.

## Utilisation par un autre addon

Déclarer la dépendance dans `addon.xml` :

```xml
<import addon="script.module.jsruntime" version="1.0.1"/>
```

puis :

```python
import jsruntime

rt = jsruntime.find()                  # ('deno', '/…/bin/deno') ou None
if rt is None:
    rt = jsruntime.install_with_dialog()  # téléchargement avec barre de progression
# yt-dlp : YoutubeDL({'js_runtimes': {rt[0]: {'path': rt[1]}}})
```

## Structure du dépôt

```
addon.xml
default.py              entrée « Programmes » : installer / mettre à jour
lib/jsruntime/          API (find, install, install_with_dialog) et téléchargement
resources/language/     traductions gettext (fr_FR, en_GB)
```

## Crédits

- **Développement :** [TheWorms](https://github.com/TheWorms).
- **Moteurs téléchargés :** [Deno](https://deno.com) (MIT) et [Node.js](https://nodejs.org)
  (MIT), depuis leurs sites officiels.

## Licence

GPL v3 ou ultérieure — voir [`LICENSE.txt`](LICENSE.txt).
