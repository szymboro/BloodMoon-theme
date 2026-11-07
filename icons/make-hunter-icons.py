#!/usr/bin/env python3
"""Build the "Hunter" icon theme: Papirus-Dark-Blood recolored to ash/bone with blood-red accents.

Re-run after Papirus updates:  python3 ~/.local/share/icons/make-hunter-icons.py
"""
import colorsys
import os
import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

ICONS = os.path.expanduser("~/.local/share/icons")
SRC = os.path.join(ICONS, "Papirus-Dark-Blood")
DST = os.path.join(ICONS, "Hunter")
CONTEXTS = {"apps", "categories", "devices", "mimetypes", "places", "emblems"}

# Ramp from the BloodMoon color scheme: near-black -> ash -> bone.
ASH = [(0.00, (14, 11, 12)), (0.25, (38, 31, 32)), (0.50, (92, 84, 80)),
       (0.75, (156, 146, 130)), (1.00, (226, 214, 188))]
# Dried blood -> fresh blood.
BLOOD = [(0.00, (34, 6, 8)), (0.35, (92, 15, 20)), (0.65, (150, 30, 32)),
         (1.00, (196, 58, 52))]


def ramp(stops, t):
    t = min(1.0, max(0.0, t))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return tuple(round(x + (y - x) * f) for x, y in zip(ca, cb))
    return stops[-1][1]


def recolor(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    hue = h * 360
    # Reds, crimsons, magentas-leaning-red become blood.
    if s > 0.3 and (hue < 40 or hue > 330) and 0.08 < l < 0.92:
        return ramp(BLOOD, l * 1.25)
    # Gentle S-curve keeps flat icons from going muddy.
    t = lum * lum * (3 - 2 * lum)
    return ramp(ASH, 0.15 + 0.85 * t if lum > 0.02 else t)


HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
NAMED = re.compile(r"(fill|stroke|stop-color|color)(\s*[:=]\s*\"?)(white|black)\b")


def sub_hex(m):
    v = m.group(1)
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return "#%02x%02x%02x" % recolor(*(int(v[i:i + 2], 16) for i in (0, 2, 4)))


def transform(svg):
    svg = NAMED.sub(lambda m: m.group(1) + m.group(2) + ("#ffffff" if m.group(3) == "white" else "#000000"), svg)
    return HEX.sub(sub_hex, svg)


def build_one(job):
    real, out = job
    try:
        with open(real, encoding="utf-8") as f:
            data = f.read()
        with open(out, "w", encoding="utf-8") as f:
            f.write(transform(data))
    except (OSError, UnicodeDecodeError):
        shutil.copyfile(real, out)


def mirror(src, dst):
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        for name in os.listdir(src):
            mirror(os.path.join(src, name), os.path.join(dst, name))
    elif os.path.exists(src) and not os.path.lexists(dst):
        os.symlink(os.path.realpath(src), dst)


def main():
    if os.path.exists(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    jobs, links, done = [], [], {}
    for size in sorted(os.listdir(SRC)):
        sdir = os.path.join(SRC, size)
        if not os.path.isdir(sdir):
            continue
        for ctx in os.listdir(sdir):
            if ctx not in CONTEXTS:
                # Tray/toolbar icons stay as they were: mirror them as links so
                # they're found here before the recolored device/app icons.
                mirror(os.path.join(sdir, ctx), os.path.join(DST, size, ctx))
                continue
            cdir = os.path.join(sdir, ctx)
            odir = os.path.join(DST, size, ctx)
            os.makedirs(odir, exist_ok=True)
            for name in os.listdir(cdir):
                real = os.path.realpath(os.path.join(cdir, name))
                if not os.path.isfile(real):
                    continue
                out = os.path.join(odir, name)
                if real in done:
                    links.append((done[real], out))
                else:
                    done[real] = out
                    jobs.append((real, out))
    with ProcessPoolExecutor() as ex:
        list(ex.map(build_one, jobs, chunksize=256))
    for target, out in links:
        os.symlink(os.path.relpath(target, os.path.dirname(out)), out)

    # Same directory list as the source, but name/inheritance changed.
    with open(os.path.join(SRC, "index.theme")) as f:
        idx = f.read()
    idx = re.sub(r"^Name=.*$", "Name=Hunter", idx, count=1, flags=re.M)
    idx = re.sub(r"^Comment=.*$", "Comment=Ash, bone and old blood (Papirus based)", idx, count=1, flags=re.M)
    idx = re.sub(r"^Inherits=.*$", "Inherits=Papirus-Dark-Blood,breeze-dark,hicolor", idx, count=1, flags=re.M)
    with open(os.path.join(DST, "index.theme"), "w") as f:
        f.write(idx)
    write_volume_icons()
    print(f"{len(jobs)} icons recolored, {len(links)} links")


# Volume icons: a hunter's bell with sound arcs. Drawn on a 22px grid, uses the
# Plasma color scheme classes so the panel recolors them.
BELL_STYLE = (".ColorScheme-Text { color:#d8cbb0; } .ColorScheme-NegativeText { color:#c43a34; } "
              ".ColorScheme-NeutralText { color:#c4813a; }")
BELL = ('<g transform="rotate(-20 8 10)">'
        '<rect class="ColorScheme-Text" style="fill:currentColor" x="7" y="0.4" width="2" height="4.2" rx="1"/>'
        '<rect class="ColorScheme-Text" style="fill:currentColor" x="5.9" y="4.2" width="4.2" height="1.2" rx="0.5"/>'
        '<path class="ColorScheme-Text" style="fill:currentColor" d="M 5.6,5.8 H 10.4 '
        'C 11.2,7 11.6,8.6 11.6,10.4 V 12.4 L 13.6,15.6 H 2.4 L 4.4,12.4 V 10.4 C 4.4,8.6 4.8,7 5.6,5.8 Z"/>'
        '<circle class="ColorScheme-Text" style="fill:currentColor" cx="9.6" cy="17.1" r="1.4"/></g>')
ARCS = ["M 14.6,7.4 A 3.4,3.4 0 0 1 14.6,11.6",
        "M 16.3,5.4 A 5.8,5.8 0 0 1 16.3,13.6",
        "M 18,3.4 A 8.2,8.2 0 0 1 18,15.6"]


def bell_svg(level, cls="ColorScheme-Text"):
    body = BELL
    if level < 0:  # muted: bell with a slash, no clapper motion
        body += ('<path class="ColorScheme-NegativeText" style="fill:none;stroke:currentColor;'
                 'stroke-width:1.6;stroke-linecap:round" d="M 15,6 21,12 M 21,6 15,12"/>')
    else:
        for i, d in enumerate(ARCS):
            on = i < level
            body += (f'<path class="{cls if on else "ColorScheme-Text"}" style="fill:none;stroke:currentColor;'
                     f'stroke-width:1.5;stroke-linecap:round;opacity:{1 if on else 0.3}" d="{d}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">'
            f'<defs><style id="current-color-scheme" type="text/css">{BELL_STYLE}</style></defs>{body}</svg>\n')


def write_volume_icons():
    icons = {"audio-volume-high": bell_svg(3), "audio-volume-medium": bell_svg(2),
             "audio-volume-low": bell_svg(1), "audio-volume-low-zero": bell_svg(0),
             "audio-volume-off": bell_svg(0), "audio-volume-muted": bell_svg(-1),
             "audio-volume-muted-blocking": bell_svg(-1), "audio-volume-muted-blocked": bell_svg(-1),
             "audio-off": bell_svg(-1),
             "audio-volume-high-warning": bell_svg(3, "ColorScheme-NeutralText"),
             "audio-volume-high-danger": bell_svg(3, "ColorScheme-NegativeText")}
    for size in ("16x16", "22x22", "24x24"):
        for sub in ("panel", "symbolic/status"):
            d = os.path.join(DST, size, sub)
            os.makedirs(d, exist_ok=True)
            for name, svg in icons.items():
                for suffix in ("", "-panel", "-symbolic"):
                    path = os.path.join(d, name + suffix + ".svg")
                    if os.path.lexists(path):
                        os.unlink(path)  # never write through a link into the system theme
                    with open(path, "w") as f:
                        f.write(svg)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--one":  # preview: recolor one file to stdout
        sys.stdout.write(transform(open(sys.argv[2]).read()))
    else:
        main()
