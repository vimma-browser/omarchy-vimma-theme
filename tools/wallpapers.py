#!/usr/bin/env python3
"""Draw the terminal-style wallpapers (2-* and up) in backgrounds/.

Each is written as SVG and rendered with rsvg-convert, then saved as JPEG with ImageMagick, so the
text is laid out on a character grid in JetBrains Mono as a terminal would draw it. Needs
rsvg-convert, magick and the JetBrainsMono Nerd Font. Run from anywhere:
    python3 tools/wallpapers.py
"""

import base64
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "backgrounds"
LOGO = ROOT / "tools" / "logo.png"

W, H = 3840, 2400
FONT = "JetBrainsMono Nerd Font"
FS = 46  # font size: about 140 columns across, a large terminal
CW = FS * 0.6  # JetBrains Mono's advance is 0.6 em
LH = round(FS * 1.55)

# The palette, from colors.toml.
C = {
    "accent": "#2cf5d2",
    "selection": "#123532",
    "muted": "#234040",
    "bg": "#071011",
    "bg_dark": "#050c0d",
    "bg_darker": "#030708",
    "bg_light": "#0e1b1c",
    "fg": "#c2d6d3",
    "fg_dark": "#7f9a96",
    "fg_bright": "#f5fffd",
    "red": "#ff6b6b",
    "yellow": "#f2c94c",
    "orange": "#f59e5b",
    "green": "#9be37a",
    "cyan": "#5cc8f0",
    "blue": "#7b9cf5",
    "magenta": "#ff4fb8",
    "brown": "#a67c52",
    "bright_magenta": "#c79bf0",
    "bright_blue": "#a9c0ff",
}


class Svg:
    def __init__(self, bg=C["bg"]):
        self.parts = [f'<rect width="{W}" height="{H}" fill="{bg}"/>']

    def raw(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill, rx=0, stroke=None, sw=0, opacity=1):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}'
            f' opacity="{opacity}"/>'
        )

    def text(self, x, y, s, fill=C["fg"], size=FS, weight=400, anchor="start", opacity=1):
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}"'
            f' fill="{fill}" text-anchor="{anchor}" opacity="{opacity}" xml:space="preserve">'
            f"{escape(s)}</text>"
        )

    def spans(self, x, y, runs, size=FS, weight=400):
        """One line of differently coloured runs, laid out on the character grid."""
        col = 0
        for s, fill in runs:
            self.text(x + col * size * 0.6, y, s, fill, size, weight)
            col += len(s)

    def badge(self, x, y, label, bg, size=FS, pad=0.9, fg=C["bg"]):
        """A status-bar badge: bold label on a colour block; y is the text baseline."""
        w = (len(label) + 2 * pad) * size * 0.6
        h = size * 1.5
        self.rect(x, y - size * 1.08, w, h, bg, rx=size * 0.12)
        self.text(x + pad * size * 0.6, y, label, fg, size, 700)
        return w

    def cursor(self, x, y, size=FS, fill=C["accent"], char="", hollow=False):
        if hollow:
            self.rect(x, y - size * 0.95, size * 0.6, size * 1.25, "none", stroke=fill, sw=4)
            return
        self.rect(x, y - size * 0.95, size * 0.6, size * 1.25, fill)
        if char:
            self.text(x, y, char, C["bg"], size)

    def logo(self, cx, cy, size, opacity=1):
        data = base64.b64encode(LOGO.read_bytes()).decode()
        self.parts.append(
            f'<image x="{cx - size / 2}" y="{cy - size / 2}" width="{size}" height="{size}"'
            f' opacity="{opacity}" href="data:image/png;base64,{data}"/>'
        )

    def save(self, name):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
            f' viewBox="0 0 {W} {H}">' + "".join(self.parts) + "</svg>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            src, png = Path(tmp, "w.svg"), Path(tmp, "w.png")
            src.write_text(svg)
            subprocess.run(["rsvg-convert", "-o", png, src], check=True)
            subprocess.run(["magick", png, "-quality", "92", OUT / name], check=True)
        print(OUT / name)


def vim_intro():
    """Vim's start screen: a column of tildes, the intro text, and the status and command lines."""
    s = Svg()
    top, left = 120, 120
    rows = (H - top - 140) // LH - 1
    s.cursor(left + 4 * CW, top + LH)
    s.text(left, top + LH, "  1 ", C["fg_dark"])
    for r in range(1, rows):
        s.text(left, top + LH * (r + 1), "~", C["muted"])
    cx, cy = W / 2, H / 2 - 260
    s.logo(cx, cy, 520)
    lines = [
        ("VIMMA", C["fg_bright"], 700),
        ("", None, 0),
        ("a keyboard-first browser", C["fg"], 400),
        ("Vim- and tmux-style keys, every one remappable", C["fg_dark"], 400),
        ("", None, 0),
    ]
    y = cy + 380
    for t, fill, wt in lines:
        if t:
            s.text(cx, y, t, fill, weight=wt, anchor="middle")
        y += LH
    help_rows = [
        ("type  ", "f", "             to follow a link"),
        ("type  ", "ctrl+b v", "      to split the window"),
        ("type  ", "ctrl+b ?", "      for every key"),
    ]
    width = max(len(a + b + c) for a, b, c in help_rows)
    x0 = cx - width * CW / 2
    for a, b, c in help_rows:
        s.spans(x0, y, [(a, C["fg_dark"]), (b, C["accent"]), (c, C["fg_dark"])])
        y += LH
    # Status line, then an empty command line.
    sy = top + LH * (rows + 1)
    s.rect(left - 20, sy - FS * 1.08, W - 2 * left + 40, FS * 1.5, C["bg_light"])
    w = s.badge(left - 20, sy, "NORMAL", C["accent"])
    s.text(left - 20 + w + CW, sy, "vimma.dev", C["fg"])
    s.text(W - left, sy, "utf-8   1:1   All", C["fg_dark"], anchor="end")
    s.save("2-vim-intro.jpg")


def tmux():
    """A tmux window with three panes: config.toml in Vim, a key list, and a shell."""
    s = Svg(C["bg_dark"])
    m = 60
    bar_h = LH
    split_x = W * 0.56
    split_y = (H - bar_h) * 0.52
    # Pane borders: the active pane's in the accent, the others muted.
    s.raw(
        f'<line x1="{split_x}" y1="{m}" x2="{split_x}" y2="{H - bar_h - m / 2}"'
        f' stroke="{C["accent"]}" stroke-width="5"/>'
        f'<line x1="{split_x}" y1="{split_y}" x2="{W - m}" y2="{split_y}"'
        f' stroke="{C["muted"]}" stroke-width="5"/>'
    )

    # Left pane: config.toml.
    code = [
        [("# ~/.config/vimma/config.toml", C["fg_dark"])],
        [("schema", C["blue"]), (" = ", C["fg"]), ("2", C["orange"])],
        [],
        [("[theme]", C["accent"])],
        [("name", C["blue"]), (" = ", C["fg"]), ('"vimma"', C["green"])],
        [("appearance", C["blue"]), (" = ", C["fg"]), ('"system"', C["green"])],
        [],
        [("[keys]", C["accent"])],
        [("prefix", C["blue"]), (" = ", C["fg"]), ('"ctrl+b"', C["green"]),
         ("             # as in tmux", C["fg_dark"])],
        [("toggle_sidebar", C["blue"]), (" = ", C["fg"]), ("[", C["fg"]),
         ('"prefix+b"', C["green"]), (", ", C["fg"]), ('"<leader>n"', C["green"]), ("]", C["fg"])],
        [],
        [("[modal]", C["accent"])],
        [("leader", C["blue"]), (" = ", C["fg"]), ('"space"', C["green"]),
         ("              # as in many Vim setups", C["fg_dark"])],
        [],
        [("[modal.normal]", C["accent"])],
        [('"<leader>F"', C["green"]), (" = ", C["fg"]), ('"hint.follow_new_tab_fg"', C["green"])],
    ]
    x, y = m + 20, m + LH
    rows = int((H - bar_h - m) // LH) - 2
    for i in range(rows):
        if i < len(code):
            s.text(x, y, f"{i + 1:>3} ", C["muted"] if i != 4 else C["accent"])
            if i == 4:
                s.rect(x + 4 * CW, y - FS * 1.05, split_x - x - 4 * CW - 30, LH, C["bg_light"])
            s.spans(x + 4 * CW, y, code[i])
        else:
            s.text(x, y, "~", C["muted"])
        y += LH
    s.cursor(x + 4 * CW, m + LH * 5, char="n")
    ly = m + LH * rows
    w = s.badge(x, ly, "NORMAL", C["accent"])
    s.text(x + w + CW, ly, "config.toml", C["fg"])
    s.text(split_x - 40, ly, "5:1", C["fg_dark"], anchor="end")

    # Top right: the pane keys.
    keys = [
        ("ctrl+b v", "split right"),
        ("ctrl+b -", "split down"),
        ("ctrl+b h j k l", "move between panes"),
        ("ctrl+b z", "zoom the pane"),
        ("ctrl+b r", "resize mode"),
        ("ctrl+b ?", "every key, with a filter"),
    ]
    x = split_x + 60
    y = m + LH
    s.spans(x, y, [("~ ", C["accent"]), ("❯ ", C["magenta"]), ("cat pane-keys.txt", C["fg"])])
    y += LH * 1.5
    for k, d in keys:
        s.spans(x, y, [(f"  {k:<17}", C["accent"]), (d, C["fg"])])
        y += LH

    # Bottom right: a shell.
    y = split_y + LH * 1.4
    s.spans(x, y, [("~ ", C["accent"]), ("❯ ", C["magenta"]), ("omarchy-theme-set vimma", C["fg"])])
    y += LH
    s.text(x, y, "Theme set to vimma", C["fg_dark"])
    y += LH * 1.5
    s.spans(x, y, [("~ ", C["accent"]), ("❯ ", C["magenta"])])
    s.cursor(x + 4 * CW, y, hollow=True)

    # tmux's status bar.
    by = H - bar_h / 2 + FS * 0.35
    s.rect(0, H - bar_h, W, bar_h, C["bg_light"])
    s.text(30, by, "[vimma]", C["accent"], weight=700)
    s.spans(30 + 8.5 * CW, by, [
        ("0:browse*", C["fg_bright"]), ("  1:read-", C["fg_dark"]), ("  2:agent", C["fg_dark"]),
    ])
    s.text(W - 30, by, "vimma.dev", C["fg_dark"], anchor="end")
    s.save("3-tmux.jpg")


def modes():
    """The status bar's badges, each mode in its own colour."""
    s = Svg()
    rows = [
        [("NORMAL", "accent"), ("INSERT", "green"), ("VISUAL", "magenta"), ("COMMAND", "yellow"),
         ("HINT", "orange")],
        [("ELEMENT", "bright_magenta"), ("HELP", "cyan"), ("PANEL", "blue"), ("RESIZE", "brown"),
         ("PREFIX", "red")],
    ]
    size = 64
    gap = size * 0.9
    y = H / 2 - size * 1.2
    for row in rows:
        widths = [(len(t) + 1.8) * size * 0.6 for t, _ in row]
        x = (W - sum(widths) - gap * (len(row) - 1)) / 2
        for (t, k), wdt in zip(row, widths):
            s.badge(x, y, t, C[k], size)
            x += wdt + gap
        y += size * 2.6
    cy = y + size * 0.6
    line = "vimma "
    x0 = W / 2 - (len(line) + 1) * size * 0.6 / 2
    s.text(x0, cy, line, C["fg_dark"], size)
    s.cursor(x0 + len(line) * size * 0.6, cy, size)
    s.save("4-modes.jpg")


def hints():
    """A page of text drawn as bars, with link-hint labels on its links."""
    s = Svg()
    import random

    rnd = random.Random(7)
    labels = iter("as sd df fg gh hj jk kl qw we er rt ty yu ui io op za xs cd vf bg nh mj".split())
    col_x, col_w = 900, 2040
    placed = []
    y = 300
    s.rect(col_x, y - 40, col_w * 0.55, 70, C["fg_bright"], rx=10, opacity=0.85)
    y += 160
    while y < H - 360:
        for _ in range(rnd.randint(3, 6)):
            x = col_x
            line_w = col_w * (rnd.uniform(0.55, 0.8) if rnd.random() < 0.2 else 1)
            while x < col_x + line_w - 80:
                w = rnd.randint(60, 260)
                w = min(w, col_x + line_w - x)
                link = rnd.random() < 0.07 and all(
                    abs(x - px) > 160 or abs(y - py) > 100 for px, py in placed)
                s.rect(x, y, w, 26, C["cyan"] if link else C["muted"], rx=6,
                       opacity=0.9 if link else 0.8)
                if link:
                    placed.append((x, y))
                    lab = next(labels, None)
                    if lab:
                        s.badge(x - 10, y - 4, lab.upper(), C["magenta"], 40, 0.45)
                x += w + 28
            y += 64
        y += 70
    by = H - 90
    s.rect(0, by - FS * 1.1, W, FS * 1.6, C["bg_light"])
    w = s.badge(30, by, "HINT", C["orange"])
    s.text(30 + w + CW, by, "f", C["fg"])
    s.text(W - 30, by, "type a label", C["fg_dark"], anchor="end")
    s.save("5-hints.jpg")


def hjkl():
    """h j k l as keycaps, with the direction under each."""
    s = Svg()
    keys = [("h", "←"), ("j", "↓"), ("k", "↑"), ("l", "→")]
    size, gap = 300, 70
    x = (W - 4 * size - 3 * gap) / 2
    y = H / 2 - size / 2 - 60
    for k, arrow in keys:
        s.rect(x + 8, y + 18, size, size, C["bg_darker"], rx=40)
        s.rect(x, y, size, size, C["bg_light"], rx=40, stroke=C["accent"], sw=8)
        s.text(x + size / 2, y + size * 0.66, k, C["accent"], 190, 700, "middle")
        s.text(x + size / 2, y + size + 170, arrow, C["fg_dark"], 90, 400, "middle")
        x += size + gap
    s.save("6-hjkl.jpg")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    vim_intro()
    tmux()
    modes()
    hints()
    hjkl()
