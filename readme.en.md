[Français](README.md) · **English**

# JavaScript engine for Kodi

<!-- version:auto -->
**Version : 1.0.2**
<!-- /version:auto -->

Kodi module that installs a **JavaScript engine** (Deno or Node.js) for add-ons that need one.
It is used by [Wtube](https://github.com/TheWorms/kodi-addon-youtube): yt-dlp has to run
YouTube's JavaScript challenges, otherwise videos are blocked.

The binary (40 to 100 MB) is **not shipped in the zip**: it is downloaded once, in the right
format for the device, and kept in `addon_data/script.module.jsruntime/bin/`, which updates
never touch.

| System | Downloaded engine |
|--------|-------------------|
| 64-bit ARM Linux (aarch64) — 64-bit CoreELEC / LibreELEC | Deno |
| 64-bit x86 Linux | Deno |
| 32-bit ARM Linux (armv7 userland) | Node.js 22 (Deno has no 32-bit build) |

## Installation

**Recommended — TheWorms repository** (automatic updates). The module is installed
automatically with the add-ons that depend on it.

Download the repository by clicking **[HERE](https://raw.githubusercontent.com/TheWorms/kodi-repo/main/zips/repository.theworms/repository.theworms.zip)**, then in Kodi:

1. **Add-ons** → **Install from zip file** → select the downloaded zip
   *(if Kodi blocks it, enable **Unknown sources** under Settings → Add-ons)*
2. **Install from repository** → **TheWorms Repository** → **Program add-ons** → **JavaScript engine**

Then run **Programs → JavaScript engine**: a progress bar follows the download and a
notification shows the installed version. Run it again to update the engine.

**Manual install (alternative):** download the zip from the [Releases](../../releases) page, then **Add-ons** → **Install from zip file**.

## Use from another add-on

Declare the dependency in `addon.xml`:

```xml
<import addon="script.module.jsruntime" version="1.0.1"/>
```

then:

```python
import jsruntime

rt = jsruntime.find()                  # ('deno', '/…/bin/deno') or None
if rt is None:
    rt = jsruntime.install_with_dialog()  # download with a progress bar
# yt-dlp: YoutubeDL({'js_runtimes': {rt[0]: {'path': rt[1]}}})
```

## Repository layout

```
addon.xml
default.py              "Programs" entry: install / update
lib/jsruntime/          API (find, install, install_with_dialog) and download
resources/language/     gettext translations (fr_FR, en_GB)
```

## Credits

- **Development:** [TheWorms](https://github.com/TheWorms).
- **Downloaded engines:** [Deno](https://deno.com) (MIT) and [Node.js](https://nodejs.org)
  (MIT), from their official sites.

## License

GPL v3 or later — see [`LICENSE.txt`](LICENSE.txt).
