#!/usr/bin/env bash
# Blood Moon theme installer for KDE Plasma 6 (Fedora).
#
#   ./install.sh                 install and apply everything
#   ./install.sh kde librewolf   only the parts you name
#
# Parts: kde, icons, fonts, vscode, librewolf
# Add --vscode-settings to also copy the de-bloated VS Code settings.json
# (your existing one is backed up first).

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
STAMP="$(date +%Y%m%d-%H%M%S)"

parts=()
vscode_settings=0
for a in "$@"; do
  case "$a" in
    --vscode-settings) vscode_settings=1 ;;
    kde|icons|fonts|vscode|librewolf) parts+=("$a") ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "Unknown option: $a" >&2; exit 1 ;;
  esac
done
[ ${#parts[@]} -eq 0 ] && parts=(fonts icons kde vscode librewolf)
want() { [[ " ${parts[*]} " == *" $1 "* ]]; }

say()  { printf '\e[38;2;201;164;92m==>\e[0m %s\n' "$*"; }
warn() { printf '\e[38;2;192;57;43m!!\e[0m %s\n' "$*"; }

backup() { [ -e "$1" ] && cp -a "$1" "$1.bak-$STAMP" && echo "    backed up $1"; true; }

plasma_script() {
  local q
  q="$(command -v qdbus6 || command -v qdbus-qt6 || command -v qdbus || true)"
  [ -n "$q" ] && "$q" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$1" >/dev/null 2>&1
}

# ---------------------------------------------------------------- fonts
if want fonts; then
  say "Fonts: Cinzel (window titles)"
  mkdir -p "$DATA/fonts/Cinzel"
  cp "$HERE/fonts/"* "$DATA/fonts/Cinzel/"
  fc-cache -f "$DATA/fonts" >/dev/null 2>&1 || true
fi

# ---------------------------------------------------------------- icons
if want icons; then
  say "Icons: Papirus-Dark-Blood + Hunter"
  if [ ! -d /usr/share/icons/Papirus-Dark ]; then
    warn "Papirus is not installed. Run:  sudo dnf install papirus-icon-theme"
    warn "then re-run:  $0 icons"
  else
    mkdir -p "$DATA/icons/custom"
    rm -rf "$DATA/icons/Papirus-Dark-Blood"
    tar -xJf "$HERE/icons/Papirus-Dark-Blood.tar.xz" -C "$DATA/icons"
    cp "$HERE/icons/make-hunter-icons.py" "$DATA/icons/"
    say "Building Hunter icons (recolors ~35k icons, takes a minute)..."
    python3 "$DATA/icons/make-hunter-icons.py"
    for t in Papirus-Dark-Blood Hunter; do
      gtk-update-icon-cache -qf "$DATA/icons/$t" 2>/dev/null || true
    done
  fi
fi

# ---------------------------------------------------------------- KDE
if want kde; then
  say "KDE: color scheme, icons, title font, start menu rune"
  mkdir -p "$DATA/color-schemes" "$DATA/icons/custom"
  cp "$HERE/kde/BloodMoon.colors" "$DATA/color-schemes/"
  cp "$HERE/kde/hunter-rune.png" "$DATA/icons/custom/"
  plasma-apply-colorscheme BloodMoon >/dev/null 2>&1 || warn "could not apply color scheme (not in a Plasma session?)"
  kwriteconfig6 --file kdeglobals --group General --key AccentColor "130,26,26"
  kwriteconfig6 --file kdeglobals --group General --key accentColorFromWallpaper false
  if fc-list | grep -qi cinzel; then
    kwriteconfig6 --file kdeglobals --group WM --key activeFont "Cinzel,11,-1,5,700,0,0,0,0,0,0,0,0,0,0,1"
  fi
  if [ -d "$DATA/icons/Hunter" ] && [ -x /usr/libexec/plasma-changeicons ]; then
    /usr/libexec/plasma-changeicons Hunter >/dev/null 2>&1 || true
  fi
  plasma_script "
    panels().forEach(function (p) {
      p.widgets().forEach(function (w) {
        if (w.type === 'org.kde.plasma.kickoff' || w.type === 'org.kde.plasma.kicker') {
          w.currentConfigGroup = ['General'];
          w.writeConfig('icon', '$DATA/icons/custom/hunter-rune.png');
          w.reloadConfig();
        }
      });
    });" || warn "could not set the start menu icon (Plasma not running?)"
fi

# ---------------------------------------------------------------- VS Code
if want vscode; then
  code_bin="$(command -v code || command -v codium || true)"
  if [ -z "$code_bin" ]; then
    warn "VS Code / VSCodium not found - skipping its theme"
  else
    say "VS Code: Blood Moon theme ($(basename "$code_bin"))"
    "$code_bin" --install-extension "$HERE/vscode/bloodmoon-theme.vsix" --force >/dev/null
    case "$(basename "$code_bin")" in
      codium) cfg="$HOME/.config/VSCodium/User/settings.json" ;;
      *)      cfg="$HOME/.config/Code/User/settings.json" ;;
    esac
    mkdir -p "$(dirname "$cfg")"
    if [ "$vscode_settings" = 1 ]; then
      backup "$cfg"
      cp "$HERE/vscode/settings.json" "$cfg"
      echo "    copied de-bloated settings.json"
    elif [ ! -s "$cfg" ]; then
      printf '{\n  "workbench.colorTheme": "Blood Moon"\n}\n' > "$cfg"
    else
      echo "    pick it in VS Code: Ctrl+K Ctrl+T -> Blood Moon"
      echo "    (or re-run with --vscode-settings for the full de-bloated config)"
    fi
  fi
fi

# ---------------------------------------------------------------- LibreWolf
if want librewolf; then
  prof=""
  for base in "$HOME/.config/librewolf/librewolf" "$HOME/.librewolf"; do
    ini="$base/installs.ini"; [ -f "$ini" ] || ini="$base/profiles.ini"
    [ -f "$ini" ] || continue
    rel="$(grep -m1 '^Default=' "$ini" | cut -d= -f2-)"
    if [ -n "$rel" ]; then
      case "$rel" in /*) prof="$rel" ;; *) prof="$base/$rel" ;; esac
      [ -d "$prof" ] && break
      prof=""
    fi
  done
  if [ -z "$prof" ]; then
    warn "No LibreWolf profile found - open LibreWolf once, then re-run:  $0 librewolf"
  else
    say "LibreWolf: square tabs + Blood Moon UI  ($(basename "$prof"))"
    mkdir -p "$prof/chrome"
    for f in userChrome.css userContent.css; do
      backup "$prof/chrome/$f"
      cp "$HERE/librewolf/$f" "$prof/chrome/"
    done
    touch "$prof/user.js"
    while IFS= read -r line; do
      case "$line" in user_pref*)
        key="${line#*\"}"; key="${key%%\"*}"
        grep -q "\"$key\"" "$prof/user.js" || echo "$line" >> "$prof/user.js" ;;
      esac
    done < "$HERE/librewolf/user.js"
    pgrep -x librewolf >/dev/null && warn "Restart LibreWolf to see the theme"
  fi
fi

say "Done. Log out and back in if anything looks half-applied."
