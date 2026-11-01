#!/usr/bin/env python3
"""Clean, premium README art in the language of heedeo.com and naamchelabs.com:
Geist with tight tracking, grey second lines, mono figure labels, ASCII texture,
square corners. Every piece is drawn twice, for GitHub's light and dark themes.

    python3 tools/premium.py
"""
import base64, html, io, math, os, random
from fontTools import subset
from fontTools.ttLib import TTFont


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")
OUT = os.path.join(ROOT, "assets")

THEMES = {
    "dark": dict(bg="#07080b", card="#0a0b0f", line="#1d2029", fg="#f4f4f3", grey="#8b8b93", dim="#4b4d55",
                 tex="#ffffff", tex_op=.07, acc="#5b6cff", acc2="#a5b4fc", warn="#f59e0b", bad="#ef4444",
                 pupil="#0b0b0f", white="#eef1ff", chip="#12141b"),
    "light": dict(bg="#f6f6f4", card="#ffffff", line="#e4e4e0", fg="#0b0b0a", grey="#8a8a85", dim="#b4b4ae",
                  tex="#0b0b0a", tex_op=.08, acc="#2a3fff", acc2="#6b7cff", warn="#d97706", bad="#dc2626",
                  pupil="#0b0b0a", white="#a9b3ff", chip="#f1f1ee"),
}

FACES = {
    "geist": ("Geist-Regular.ttf", 400), "geist5": ("Geist-Medium.ttf", 500),
    "mono": ("GeistMono-Regular.ttf", 400), "deva": ("NotoSansDevanagari-Medium.ttf", 500),
}
_metrics = {}


def esc(s):
    return html.escape(s, quote=True)


def width(text, face, size, track=0.0):
    """Advance width of `text` in px, from the font's own metrics."""
    if face not in _metrics:
        f = TTFont(os.path.join(FONTS, FACES[face][0]))
        _metrics[face] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[face]
    w = sum(hmtx.get(cmap.get(ord(c), ".notdef"), (500, 0))[0] for c in text)
    return w / upm * size + track * size * max(len(text) - 1, 0)


class Art:
    def __init__(self, theme, w, h, title):
        self.t, self.w, self.h, self.title = THEMES[theme], w, h, title
        self.parts, self.defs, self.used, self.n = [], [], {}, 0

    def id(self, p="i"):
        self.n += 1
        return f"{p}{self.n}"

    def use(self, face, s):
        self.used.setdefault(face, set()).update(s)

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, face="geist", size=16, fill="fg", track=0.0, anchor="start", extra=""):
        self.use(face, s)
        fam = "deva" if face == "deva" else ("mono" if face == "mono" else "geist")
        wt = ' font-weight="500"' if face == "geist5" else ""
        ls = f' letter-spacing="{track * size:.2f}"' if track else ""
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}"{wt}{ls} '
                f'text-anchor="{anchor}" fill="{self.t.get(fill, fill)}"{extra}>{esc(s)}</text>')

    def rise(self, inner, at, dy=12):
        """Fade and lift into place, once. Visible by default, so viewers that do
        not run SVG animation still see the final frame."""
        d = at + .9
        k = f"0;{at / d:.3f};1"
        spl = "0 0 1 1;.2 .7 .2 1"
        return (f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="{k}" dur="{d:.2f}s" fill="freeze" '
                f'calcMode="spline" keySplines="{spl}"/>'
                f'<animateTransform attributeName="transform" type="translate" values="0 {dy};0 {dy};0 0" keyTimes="{k}" '
                f'dur="{d:.2f}s" fill="freeze" calcMode="spline" keySplines="{spl}"/>{inner}</g>')

    def faces_css(self):
        css = []
        for face, chars in self.used.items():
            fname, wt = FACES[face]
            fam = {"geist5": "geist"}.get(face, face)
            f = TTFont(os.path.join(FONTS, fname))
            o = subset.Options()
            o.flavor, o.layout_features, o.name_IDs, o.notdef_outline = "woff", ["*"], [], True
            sub = subset.Subsetter(o)
            sub.populate(text="".join(chars) + " ")
            sub.subset(f)
            f.flavor = "woff"
            b = io.BytesIO()
            f.save(b)
            css.append(f"@font-face{{font-family:{fam};font-weight:{wt};"
                       f"src:url(data:font/woff;base64,{base64.b64encode(b.getvalue()).decode()}) format('woff')}}")
        return "".join(css)

    def save(self, name):
        t = self.t
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
               f'<title>{esc(self.title)}</title><style>{self.faces_css()}'
               f'text{{white-space:pre;font-variant-ligatures:none}}</style><defs>{"".join(self.defs)}</defs>'
               f'<rect x=".5" y=".5" width="{self.w - 1}" height="{self.h - 1}" fill="{t["card"]}" stroke="{t["line"]}"/>'
               f'{"".join(self.parts)}'
               f'<rect x="0" y="0" width="36" height="2" fill="{t["acc"]}"/></svg>')
        path = os.path.join(OUT, name)
        with open(path, "w") as fh:
            fh.write(svg)
        return path


def ascii_field(a, x0, y0, x1, y1, seed, mask_id=None, twinkles=70):
    rnd = random.Random(seed)
    t = a.t
    cw, lh, size = 9.0, 16, 12
    rows = []
    chars = " " * 14 + ".:-=+*#%"
    for r in range(int((y1 - y0) / lh)):
        s = "".join(rnd.choice(chars) for _ in range(int((x1 - x0) / cw)))
        rows.append(a.text(x0, y0 + 12 + r * lh, s, "mono", size, t["tex"], extra=f' opacity="{t["tex_op"]}"'))
    tw = []
    for k in range(twinkles):
        cx = x0 + rnd.randrange(int((x1 - x0) / cw)) * cw
        cy = y0 + 12 + rnd.randrange(int((y1 - y0) / lh)) * lh
        ch = rnd.choice("+*#=%")
        d = rnd.uniform(2.5, 6)
        a.use("mono", ch)
        tw.append(f'<text x="{cx:.1f}" y="{cy}" font-family="mono" font-size="{size}" fill="{t["acc"]}" opacity="0">{ch}'
                  f'<animate attributeName="opacity" values="0;.85;0" dur="{d:.1f}s" begin="{rnd.uniform(0, 6):.1f}s" '
                  f'repeatCount="indefinite"/></text>')
    m = f' mask="url(#{mask_id})"' if mask_id else ""
    return f'<g{m}>{"".join(rows)}{"".join(tw)}</g>'


def ascii_nazar(a, cx, cy, rows=21, inner_anim=""):
    """The evil eye drawn in mono characters, rings breathing outward."""
    t = a.t
    cw, lh, size = 8.4, 15, 14
    cols = round(rows * lh / cw)
    R = rows / 2 * lh
    rings = {k: [] for k in range(5)}
    spec = [(.2, "#", t["pupil"]), (.38, "o", "#6cc3e8"), (.58, "@", t["white"]), (.93, "#", t["acc"]), (1.0, "*", t["acc2"])]
    for r in range(rows):
        line = {k: [" "] * cols for k in rings}
        for c in range(cols):
            dx = (c + .5 - cols / 2) * cw
            dy = (r + .5 - rows / 2) * lh
            d = math.hypot(dx, dy) / R
            for k, (lim, ch, _) in enumerate(spec):
                if d <= lim:
                    line[k][c] = ch
                    break
        for k in rings:
            s = "".join(line[k])
            if s.strip():
                rings[k].append((r, s))
    out, inner = [], []
    x0, y0 = cx - cols * cw / 2, cy - rows * lh / 2
    for k, (lim, ch, color) in enumerate(spec):
        rows_svg = "".join(a.text(x0, y0 + 11 + r * lh, s, "mono", size, color) for r, s in rings[k])
        g = (f'<g><animate attributeName="opacity" values=".55;1;.55" dur="3.6s" begin="{k * .25:.2f}s" '
             f'repeatCount="indefinite"/>{rows_svg}</g>')
        (inner if k < 2 else out).append(g)
    return "".join(out) + f'<g>{inner_anim}{"".join(inner)}</g>'


# ---------------------------------------------------------------------------

def hero(theme):
    """A bead leaves the big eye and hops word to word like a karaoke ball. Each
    word it lands on does its own thing (hey waves, arjan ripples, build drops
    back in letter by letter, break cracks, things glitches), then the bead flies
    home and the eye blinks shut on it. One loop; every animation shares the clock."""
    a = Art(theme, 1200, 520, "hey, i'm arjan.")
    t = a.t
    mk = a.id("m")
    a.defs.append(f'<radialGradient id="{mk}g" cx="84%" cy="50%" r="62%"><stop offset="0" stop-color="#fff"/>'
                  f'<stop offset=".55" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
                  f'<mask id="{mk}"><rect width="1200" height="520" fill="url(#{mk}g)"/></mask>'
                  f'<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{t["acc"]}" stop-opacity=".22"/>'
                  f'<stop offset="1" stop-color="{t["acc"]}" stop-opacity="0"/></radialGradient>')
    a.add(ascii_field(a, 1, 1, 1199, 519, 7, mk))

    # ---- layout ----------------------------------------------------------
    x0, size, tr = 72, 70, -.045
    lines = [("hey, i'm arjan.", 246, "fg"), ("i build and break things.", 320, "dim")]
    words = {}
    for text, base, col in lines:
        k = 0
        for w in text.split(" "):
            start = x0 + (width(text[:k], "geist", size, tr) + tr * size if k else 0)
            words[w] = dict(x=start, w=width(w, "geist", size, tr), base=base, col=col)
            k += len(w) + 1
    eye_cx, eye_cy = 1000, 262

    # ---- timeline --------------------------------------------------------
    stops = [("hey,", 1.35), ("i'm", .22), ("arjan.", 1.4), ("i", .22), ("build", 1.5), ("and", .22), ("break", 1.45), ("things.", .4)]
    t_spawn = .45
    times, tcur = {}, t_spawn + .8           # first hop is the long one out of the eye
    for i, (w, hold) in enumerate(stops):
        if i:
            tcur += .42
        times[w] = tcur
        tcur += hold
    depart = {w: times[w] + h for w, h in stops}
    t_home = tcur + .7
    T = round(t_home + 1.6, 2)

    def kt(*pairs):
        ks = ";".join(f"{min(max(tm / T, 0), 1):.4f}" for tm, _ in pairs)
        vs = ";".join(str(v) for _, v in pairs)
        return ks, vs

    def anim(attr, pairs, kind=None, discrete=False):
        ks, vs = kt(*pairs)
        cm = ' calcMode="discrete"' if discrete else ""
        if kind:
            return (f'<animateTransform attributeName="transform" type="{kind}" values="{vs}" keyTimes="{ks}"{cm} '
                    f'dur="{T}s" repeatCount="indefinite" additive="sum"/>')
        return f'<animate attributeName="{attr}" values="{vs}" keyTimes="{ks}"{cm} dur="{T}s" repeatCount="indefinite"/>'

    def lit(d, tl):
        """Fill: top line flashes blue; the grey line lights up and stays lit."""
        if d["col"] == "dim":
            return anim("fill", [(0, t["dim"]), (tl, t["dim"]), (tl + .12, t["fg"]), (T - .7, t["fg"]), (T - .25, t["dim"]), (T, t["dim"])])
        return ""                     # top line stays put

    def txt(s, x, fill_anim, col=None, extra=""):
        el = a.text(x, 0, s, "geist", size, col or t["dim"], tr, extra=extra)
        return el.replace("</text>", fill_anim + "</text>") if fill_anim else el

    def letters(w):
        out, k = [], 0
        for i, ch in enumerate(w):
            off = width(w[:i], "geist", size, tr) + (tr * size if i else 0)
            out.append((ch, off))
        return out

    def place(d, inner):
        return f'<g transform="translate({d["x"] + d["w"] / 2:.1f} {d["base"]})">{inner}</g>'

    # ---- effects ----------------------------------------------------------
    def fx_squash(w, d, tl):
        sq = anim("", [(0, "1 1"), (tl, "1 1"), (tl + .07, "1.05 .86"), (tl + .2, ".98 1.04"), (tl + .32, "1 1"), (T, "1 1")], "scale")
        return place(d, f'<g>{sq}{txt(w, -d["w"] / 2, lit(d, tl), t[d["col"]])}</g>')

    def fx_wave(w, d, tl):
        rot = anim("", [(0, "0 0 0"), (tl, "0 0 0"), (tl + .1, "-9 0 0"), (tl + .22, "7 0 0"), (tl + .34, "-5 0 0"), (tl + .46, "3 0 0"), (tl + .56, "0 0 0"), (T, "0 0 0")], "rotate")
        return place(d, f'<g>{rot}{txt(w, -d["w"] / 2, lit(d, tl), t[d["col"]])}</g>')

    def fx_decode(w, d, tl):
        """arjan. scrambles like a cipher, resolves into आर्जन, scrambles, settles back."""
        rnd = random.Random(21)
        glyphs = "#%&@$*+=/\\<>{}[]01xX?!"
        x = -d["w"] / 2
        frames = []                       # (start, end, svg)
        k = tl
        for _ in range(6):                # scramble in
            sc = "".join(rnd.choice(glyphs) for _ in w)
            frames.append((k, k + .055, a.text(x, 0, sc, "geist", size, "acc", tr)))
            k += .055
        frames.append((k, k + .95, a.text(x + 2, 2, "आर्जन", "deva", 64, "acc")))
        k += .95
        for _ in range(5):                # scramble out
            sc = "".join(rnd.choice(glyphs) for _ in w)
            frames.append((k, k + .055, a.text(x, 0, sc, "geist", size, "acc", tr)))
            k += .055
        end = k
        out = []
        hide = anim("opacity", [(0, 1), (tl, 1), (tl + .001, 0), (end, 0), (end + .001, 1), (T, 1)], discrete=True)
        out.append(f'<g>{hide}{txt(w, x, lit(d, end), t[d["col"]])}</g>')
        for st, en, el in frames:
            op = anim("opacity", [(0, 0), (st, 1), (en, 0), (T, 0)], discrete=True)
            out.append(f'<g opacity="0">{op}{el}</g>')
        return place(d, "".join(out))

    def fx_build(w, d, tl):
        """bits pour out of "build" into a progress bar that fills, then: shipped."""
        rnd = random.Random(8)
        L = d["x"]
        bar_y, bar_w = d["base"] + 34, 190
        out = []
        # the word flashes as it starts compiling
        out.append(place(d, txt(w, -d["w"] / 2, anim("fill", [(0, t["dim"]), (tl, t["dim"]), (tl + .08, t["acc"]),
                                                                 (tl + .9, t["acc"]), (tl + 1.2, t["fg"]), (T - .7, t["fg"]),
                                                                 (T - .25, t["dim"]), (T, t["dim"])]))))
        # bits flowing out of the bottom of the word into the bar
        for n in range(36):
            ch = rnd.choice("01")
            sx = L + rnd.uniform(4, d["w"] - 4)
            ex = L + rnd.uniform(0, bar_w)
            st = tl + .05 + n * .022
            path = f"M{sx:.0f} {d['base'] + 6} Q{(sx + ex) / 2:.0f} {d['base'] + 18} {ex:.0f} {bar_y + 4}"
            op = anim("opacity", [(0, 0), (st, 0), (st + .03, 1), (st + .28, 1), (st + .34, 0), (T, 0)])
            a.use("mono", ch)
            out.append(f'<text font-family="mono" font-size="14" fill="{t["acc"]}" opacity="0">{ch}{op}'
                       f'<animateMotion path="{path}" keyPoints="0;0;1;1" keyTimes="0;{st / T:.4f};{(st + .34) / T:.4f};1" '
                       f'calcMode="linear" dur="{T}s" repeatCount="indefinite"/></text>')
        # progress bar + label
        show = anim("opacity", [(0, 0), (tl + .05, 0), (tl + .15, 1), (tl + 1.35, 1), (tl + 1.6, 0), (T, 0)])
        fillw = anim("width", [(0, 0), (tl + .15, 0), (tl + .95, bar_w), (T, bar_w)])
        lab1 = anim("opacity", [(0, 1), (tl + .95, 1), (tl + .96, 0), (T, 0)], discrete=True)
        lab2 = anim("opacity", [(0, 0), (tl + .95, 0), (tl + .96, 1), (T, 1)], discrete=True)
        out.append(f'<g opacity="0">{show}'
                   f'<rect x="{L:.1f}" y="{bar_y}" width="{bar_w}" height="10" fill="none" stroke="{t["line"]}"/>'
                   f'<rect x="{L:.1f}" y="{bar_y}" width="0" height="10" fill="{t["acc"]}">{fillw}</rect>'
                   f'<g>{lab1}{a.text(L + bar_w + 14, bar_y + 8, "building...", "mono", 13, "grey")}</g>'
                   f'<g opacity="0">{lab2}{a.text(L + bar_w + 14, bar_y + 8, "shipped.", "mono", 13, "acc")}</g></g>')
        return "".join(out)

    def fx_none(w, d, tl):
        return place(d, txt(w, -d["w"] / 2, lit(d, tl), t[d["col"]]))

    def fx_hey(w, d, tl):
        """hey, says hello: the letters hop one after another while a hand pops up
        above the word, waves three times from the wrist, and tucks away."""
        out = []
        for i, (ch, off) in enumerate(letters(w)):
            s0 = tl + .05 + i * .07
            hop = anim("", [(0, "0 0"), (s0, "0 0"), (s0 + .12, "0 -13"), (s0 + .24, "0 2"), (s0 + .3, "0 0"), (T, "0 0")], "translate")
            out.append(f'<g>{hop}{txt(ch, -d["w"] / 2 + off, "", t["fg"])}</g>')
        # ---- a detailed waving hand -------------------------------------------
        # drawn upright with the wrist pivot at (0, 46); fingers are separate groups
        # that flex about their own bases and lag the wave (follow-through).
        hid = a.id("h")
        a.defs.append(f'<linearGradient id="{hid}g" x1="0" y1="0" x2=".35" y2="1">'
                      f'<stop offset="0" stop-color="#9aa6ff"/><stop offset=".55" stop-color="{t["acc"]}"/>'
                      f'<stop offset="1" stop-color="#2f3fd9"/></linearGradient>'
                      f'<linearGradient id="{hid}c" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a37b8"/>'
                      f'<stop offset="1" stop-color="#1c2690"/></linearGradient>')
        ink, fillg = "#141c6b", f"url(#{hid}g)"
        ease = ".42 0 .58 1"

        def sanim(pairs, kind):
            ks, vs = kt(*pairs)
            n = len(pairs) - 1
            return (f'<animateTransform attributeName="transform" type="{kind}" values="{vs}" keyTimes="{ks}" '
                    f'calcMode="spline" keySplines="{";".join([ease] * n)}" dur="{T}s" repeatCount="indefinite" additive="sum"/>')

        w0 = tl + .32                                  # wave starts
        swing = [0, -26, 20, -24, 18, -12, 5, 0]       # degrees, wrist
        beats = [w0 + k * .16 for k in range(len(swing))]

        def finger(bx, by, length, wd, ang, delay, spread):
            r = wd / 2
            body = (f'<path d="M{-r} 4 V{-length + r} A{r} {r} 0 0 1 {r} {-length + r} V4 Z" fill="{fillg}" '
                    f'stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>')
            crease = "".join(f'<path d="M{-r * .55:.1f} {-length * f:.1f} q{r * .55:.1f} 2.2 {r * 1.1:.1f} 0" fill="none" '
                             f'stroke="{ink}" stroke-opacity=".55" stroke-width="1.1" stroke-linecap="round"/>' for f in (.36, .64))
            nail = (f'<path d="M{-r * .55:.1f} {-length + r * 1.5:.1f} q0 {-r * 1.05:.1f} {r * .55:.1f} {-r * 1.05:.1f} '
                    f'q{r * .55:.1f} 0 {r * .55:.1f} {r * 1.05:.1f} z" fill="#dfe4ff" fill-opacity=".55"/>')
            shine = f'<rect x="{-r * .6:.1f}" y="{-length + r * 2.2:.1f}" width="{r * .35:.1f}" height="{length * .45:.1f}" rx="{r * .17:.1f}" fill="#fff" fill-opacity=".25"/>'
            # follow-through: each finger lags the wrist and bends the other way a little
            flex = [(0, f"0 0 0"), (tl + .1, "0 0 0"), (tl + .3, f"{spread} 0 0")]
            for k, sw in enumerate(swing[1:], 1):
                flex.append((beats[k] + delay, f"{-sw * .22 + spread * (1 - k / len(swing)):.1f} 0 0"))
            flex += [(beats[-1] + delay + .15, "0 0 0"), (T, "0 0 0")]
            return (f'<g transform="translate({bx} {by}) rotate({ang})"><g>{sanim(flex, "rotate")}'
                    f'{body}{crease}{nail}{shine}</g></g>')

        fingers = "".join(finger(*f) for f in (
            (-15.5, 0, 34, 10.5, -9, .03, -5),   # index
            (-4.5, -2, 40, 11, -2, .05, -1.5),   # middle
            (6.5, -1, 37, 10.5, 5, .07, 2),      # ring
            (16.5, 3, 28, 9.5, 13, .09, 5),      # pinky
        ))
        palm = (f'<path d="M-21 -2 C-23 14 -21 30 -12 38 C-6 43 7 43 13 38 C21 31 24 16 22 0 C17 -3 -16 -4 -21 -2 Z" '
                f'fill="{fillg}" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>'
                f'<path d="M-12 16 q10 5 22 -2" fill="none" stroke="{ink}" stroke-opacity=".45" stroke-width="1.2" stroke-linecap="round"/>'
                f'<path d="M-9 26 q8 3 16 -1" fill="none" stroke="{ink}" stroke-opacity=".35" stroke-width="1.1" stroke-linecap="round"/>'
                f'<ellipse cx="-6" cy="8" rx="9" ry="5" fill="#fff" fill-opacity=".18"/>')
        tflex = [(0, "0 0 0"), (tl + .3, "-10 0 0")] + [(beats[k] + .06, f"{swing[k] * .18 - 6:.1f} 0 0") for k in range(1, len(swing))] + \
                [(beats[-1] + .2, "0 0 0"), (T, "0 0 0")]
        thumb = (f'<g transform="translate(-19 20) rotate(-48)"><g>{sanim(tflex, "rotate")}'
                 f'<path d="M-6.2 4 V-22 A6.2 6.2 0 0 1 6.2 -22 V4 Z" fill="{fillg}" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>'
                 f'<path d="M-3.4 -9 q3.4 2 6.8 0" fill="none" stroke="{ink}" stroke-opacity=".5" stroke-width="1.1" stroke-linecap="round"/>'
                 f'<path d="M-3.4 -20 q0 -6 3.4 -6 q3.4 0 3.4 6 z" fill="#dfe4ff" fill-opacity=".55"/></g></g>')
        cuff = (f'<path d="M-13 38 C-6 43 7 43 13 38 L14 52 C6 56 -6 56 -14 52 Z" fill="url(#{hid}c)" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>'
                f'<path d="M-13 45 C-5 49 6 49 13 45" fill="none" stroke="#6b78ff" stroke-opacity=".6" stroke-width="1.2"/>')
        hand = f'{fingers}{thumb}{palm}{cuff}'
        wrist = [(0, "0 0 46"), (tl + .3, "0 0 46")] + [(b, f"{sw} 0 46") for b, sw in zip(beats[1:], swing[1:])] + [(T, "0 0 46")]
        bob = [(0, "0 0"), (tl + .3, "0 0")] + [(b, f"0 {(-3 if k % 2 else 0)}") for k, b in enumerate(beats[1:], 1)] + [(T, "0 0")]
        ks, vs = kt((0, "0"), (tl + .02, "0"), (tl + .2, "1.18"), (tl + .3, ".94"), (tl + .38, "1"),
                    (beats[-1] + .1, "1"), (beats[-1] + .26, "1.06"), (beats[-1] + .42, "0"), (T, "0"))
        pop = (f'<animateTransform attributeName="transform" type="scale" values="{vs}" keyTimes="{ks}" '
               f'dur="{T}s" repeatCount="indefinite" additive="sum"/>')
        acc = t["acc"]
        lines = "".join(f'<path d="M{dx} {dy} q7 -9 0 -18" fill="none" stroke="{acc}" stroke-width="2.4" stroke-linecap="round"/>'
                        for dx, dy in ((38, -6), (46, 2)))
        lines += "".join(f'<path d="M{dx} {dy} q-7 -9 0 -18" fill="none" stroke="{acc}" stroke-width="2.4" stroke-linecap="round"/>'
                         for dx, dy in ((-40, -6), (-48, 2)))
        lop = anim("opacity", [(0, 0), (w0, 0), (w0 + .08, 1), (beats[-2], 1), (beats[-1], 0), (T, 0)])
        hx, hy = 0, -142                               # centred over the word
        out.append(f'<g transform="translate({hx:.0f} {hy})"><g transform="translate(0 46)"><g>{pop}'
                   f'<g transform="translate(0 -46)"><g opacity="0">{lop}{lines}</g>'
                   f'<g>{sanim(bob, "translate")}<g>{sanim(wrist, "rotate")}{hand}</g></g></g></g></g></g>')
        return place(d, "".join(out))

    def fx_nepali(w, d, tl):
        """arjan. becomes आर्जन while the bead sits on it."""
        on, off = tl + .2, tl + 1.15
        out_ = anim("opacity", [(0, 1), (tl + .05, 1), (on, 0), (off, 0), (off + .15, 1), (T, 1)])
        in_ = anim("opacity", [(0, 0), (tl + .05, 0), (on, 1), (off, 1), (off + .15, 0), (T, 0)])
        latin = f'<g>{out_}{txt(w, -d["w"] / 2, "", t["fg"])}</g>'
        deva = f'<g opacity="0">{in_}{a.text(-d["w"] / 2 + 2, 0, "आर्जन", "deva", 50, "acc")}</g>'
        name = place(d, latin + deva)

        return name

    def fx_blueprint(w, d, tl):
        """build traces its own outline like a blueprint, then fills in solid."""
        x = -d["w"] / 2
        solid_op = anim("opacity", [(0, 1), (tl, 1), (tl + .06, 0), (tl + .85, 0), (tl + 1.15, 1), (T, 1)])
        fill = anim("fill", [(0, t["dim"]), (tl + .8, t["dim"]), (tl + .85, t["fg"]), (T - .7, t["fg"]), (T - .25, t["dim"]), (T, t["dim"])])
        solid = f'<g>{solid_op}{txt(w, x, fill)}</g>'
        dash = anim("stroke-dashoffset", [(0, 240), (tl + .05, 240), (tl + .85, 0), (T, 0)])
        line_op = anim("opacity", [(0, 0), (tl + .03, 0), (tl + .06, 1), (tl + 1.1, 1), (tl + 1.4, 0), (T, 0)])
        outline = a.text(x, 0, w, "geist", size, "none", tr,
                         extra=f' stroke="{t["acc"]}" stroke-width="1.3" stroke-dasharray="240" stroke-dashoffset="240"')
        outline = outline.replace("</text>", dash + "</text>")
        # faint construction lines: baseline and x-height, drawn across the word
        guides = (f'<line x1="{x - 8:.0f}" y1="0" x2="{x + d["w"] + 8:.0f}" y2="0" stroke="{t["acc"]}" stroke-opacity=".5" stroke-dasharray="3 4"/>'
                  f'<line x1="{x - 8:.0f}" y1="-37" x2="{x + d["w"] + 8:.0f}" y2="-37" stroke="{t["acc"]}" stroke-opacity=".35" stroke-dasharray="3 4"/>'
                  f'<line x1="{x - 8:.0f}" y1="-51" x2="{x + d["w"] + 8:.0f}" y2="-51" stroke="{t["acc"]}" stroke-opacity=".25" stroke-dasharray="3 4"/>')
        return place(d, solid + f'<g opacity="0">{line_op}{guides}{outline}</g>')

    def fx_break(w, d, tl):
        tl += .1
        left, right = "bre", "ak"
        wl = width(left, "geist", size, tr) + tr * size
        out = []
        for part, px, dx, ang in ((left, d["x"], -14, -9), (right, d["x"] + wl, 16, 11)):
            pw = width(part, "geist", size, tr)
            mv = anim("", [(0, "0 0"), (tl, "0 0"), (tl + .12, f"{dx} -6"), (tl + .95, f"{dx * 1.1:.0f} 4"), (tl + 1.15, "0 0"), (T, "0 0")], "translate")
            rot = anim("", [(0, f"0 {pw / 2:.0f} -20"), (tl, f"0 {pw / 2:.0f} -20"), (tl + .12, f"{ang} {pw / 2:.0f} -20"),
                            (tl + .95, f"{ang * 1.3:.0f} {pw / 2:.0f} -20"), (tl + 1.15, f"0 {pw / 2:.0f} -20"), (T, f"0 {pw / 2:.0f} -20")], "rotate")
            fill = anim("fill", [(0, t["dim"]), (tl - .1, t["dim"]), (tl, t["fg"]), (T - .7, t["fg"]), (T - .25, t["dim"]), (T, t["dim"])])
            out.append(f'<g transform="translate({px:.1f} {d["base"]})"><g>{mv}<g>{rot}{txt(part, 0, fill)}</g></g></g>')
        rnd = random.Random(11)
        cx, cy = d["x"] + wl, d["base"] - 28
        for n in range(16):
            ch = rnd.choice("/\\*#+.:%")
            vx, vy = rnd.uniform(-80, 80), rnd.uniform(-95, -30)
            path = f"M{cx:.0f} {cy:.0f} q{vx * .5:.0f} {vy:.0f} {vx:.0f} {rnd.uniform(40, 115):.0f}"
            op = anim("opacity", [(0, 0), (tl, 0), (tl + .05, 1), (tl + .8, .9), (tl + 1.05, 0), (T, 0)])
            a.use("mono", ch)
            out.append(f'<text font-family="mono" font-size="15" fill="{t["acc"] if n % 3 else t["fg"]}" opacity="0">{esc(ch)}{op}'
                       f'<animateMotion path="{path}" keyPoints="0;0;1;1" keyTimes="0;{tl / T:.4f};{(tl + 1.05) / T:.4f};1" '
                       f'calcMode="linear" dur="{T}s" repeatCount="indefinite"/></text>')
        return "".join(out)

    def fx_glitch(w, d, tl):
        jit = [(0, "0 0"), (tl, "0 0")]
        rnd = random.Random(5)
        k = tl
        while k < tl + .7:
            jit.append((k, f"{rnd.choice([-7, -4, 3, 6, 9]):d} {rnd.choice([-2, 0, 2]):d}"))
            k += .06
        jit += [(tl + .72, "0 0"), (T, "0 0")]
        main = place(d, f'<g>{anim("", jit, "translate", discrete=True)}{txt(w, -d["w"] / 2, lit(d, tl), t[d["col"]])}</g>')
        ghosts = []
        for col, sh in ((t["acc"], 1), (t["bad"], -1)):
            gj = [(0, "0 0"), (tl, "0 0")]
            k = tl
            while k < tl + .7:
                gj.append((k, f"{sh * rnd.choice([6, 10, 14, 18]):d} {rnd.choice([-3, 0, 3]):d}"))
                k += .05
            gj += [(tl + .72, "0 0"), (T, "0 0")]
            op = anim("opacity", [(0, 0), (tl, 0), (tl + .02, .85), (tl + .7, .85), (tl + .72, 0), (T, 0)])
            ghosts.append(place(d, f'<g opacity="0">{op}{anim("", gj, "translate", discrete=True)}'
                                   f'{a.text(-d["w"] / 2, 0, w, "geist", size, col, tr)}</g>'))
        return "".join(ghosts) + main

    def fx_pass(w, d, tl):
        return place(d, txt(w, -d["w"] / 2, lit(d, tl), t[d["col"]]))

    effects = {"hey,": fx_hey, "i'm": fx_none, "arjan.": fx_nepali, "i": fx_none,
               "build": fx_blueprint, "and": fx_none, "break": fx_break, "things.": fx_none}

    for w, d in words.items():
        a.add(effects[w](w, d, times[w]))

    # ---- the big eye: spits the bead out, watches it, swallows it -----------
    look = [(t_spawn + .3, "0 0")]
    for w, _ in stops:
        d = words[w]
        dx = max(-11, min(11, (d["x"] + d["w"] / 2 - eye_cx) / 60))
        dy = (d["base"] - 40 - eye_cy) / 30
        look.append((times[w] - .2, f"{dx:.1f} {dy:.1f}"))
    look += [(t_home - .1, "0 0"), (T, "0 0")]
    inner = anim("", [(0, "0 0")] + look, "translate")
    bp = [(0, "1 1")]
    for b in (t_spawn - .12, t_home):
        bp += [(b - .01, "1 1"), (b + .07, "1 .06"), (b + .2, "1 1")]
    bp += [(T, "1 1")]
    pulse = anim("r", [(0, 220), (t_spawn, 220), (t_spawn + .15, 245), (t_spawn + .7, 220), (t_home, 220), (t_home + .15, 255), (t_home + .9, 220), (T, 220)])
    a.add(f'<circle cx="{eye_cx}" cy="{eye_cy}" r="220" fill="url(#glow)">{pulse}</circle>')
    a.add(f'<g transform="translate({eye_cx} {eye_cy})"><g>{anim("", bp, "scale")}'
          f'<g transform="translate({-eye_cx} {-eye_cy})">{ascii_nazar(a, eye_cx, eye_cy, rows=19, inner_anim=inner)}</g></g></g>')

    # ---- the bead ------------------------------------------------------------
    pts = [(eye_cx, eye_cy)] + [(words[w]["x"] + words[w]["w"] / 2, words[w]["base"] - 62) for w, _ in stops] + [(eye_cx, eye_cy)]
    segs, lens = [], []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        far = abs(bx - ax) > 400
        lift = 150 if far else (55 if abs(by - ay) < 20 else 40)
        qx, qy = (ax + bx) / 2, min(ay, by) - lift
        segs.append(f"Q{qx:.0f} {qy:.0f} {bx:.0f} {by:.0f}")
        L, px, py = 0, ax, ay
        for k in range(1, 41):
            u = k / 40
            nx = (1 - u) ** 2 * ax + 2 * (1 - u) * u * qx + u * u * bx
            ny = (1 - u) ** 2 * ay + 2 * (1 - u) * u * qy + u * u * by
            L += math.hypot(nx - px, ny - py)
            px, py = nx, ny
        lens.append(L)
    total = sum(lens)
    path = f"M{pts[0][0]:.0f} {pts[0][1]:.0f} " + " ".join(segs)
    leave = [t_spawn] + [depart[w] for w, _ in stops]
    land = [times[w] for w, _ in stops] + [t_home]
    ktm, kp, acc = ["0"], ["0"], 0
    for i, L in enumerate(lens):
        ktm.append(f"{leave[i] / T:.4f}"); kp.append(f"{acc / total:.4f}")
        acc += L
        ktm.append(f"{land[i] / T:.4f}"); kp.append(f"{acc / total:.4f}")
    ktm.append("1"); kp.append("1")
    bead = (f'<circle r="12" fill="{t["acc"]}"/><circle r="8" fill="{t["white"]}"/>'
            f'<circle r="5.4" fill="#6cc3e8"/><circle r="2.6" fill="#0b0b0f"/>'
            f'<ellipse cx="-4" cy="-5" rx="3.4" ry="2" fill="#fff" opacity=".45" transform="rotate(-30 -4 -5)"/>')
    grow = anim("", [(0, ".2"), (t_spawn, ".2"), (t_spawn + .25, "1"), (t_home - .25, "1"), (t_home, ".2"), (T, ".2")], "scale")
    op = anim("opacity", [(0, 0), (t_spawn - .02, 0), (t_spawn + .05, 1), (t_home - .02, 1), (t_home + .03, 0), (T, 0)])
    a.add(f'<g opacity="0">{op}<g><animateMotion path="{path}" keyPoints="{";".join(kp)}" keyTimes="{";".join(ktm)}" '
          f'calcMode="linear" dur="{T}s" repeatCount="indefinite"/><g>{grow}{bead}</g></g></g>')
    return a.save(f"hero-{theme}.svg")


def card(theme, name, fig, title, sub, meta, visual):
    a = Art(theme, 600, 340, title)
    x = 36
    a.add(a.text(x, 52, fig, "mono", 11.5, "grey", .14))
    a.add(a.text(x, 108, title, "geist", 44, "fg", -.04))
    a.add(a.text(x, 140, sub, "geist", 18, "grey", -.01))
    a.add(a.text(x, 306, meta, "mono", 11.5, "dim", .12))
    visual(a)
    return a.save(f"card-{name}-{theme}.svg")


def v_heedeo(a):
    """Visitors stream in, heedeo decides, three lanes out."""
    t = a.t
    rnd = random.Random(3)
    node_x, node_y = 330, 230
    lanes = [("allow", 196, t["acc"], .68), ("challenge", 230, t["acc2"], .2), ("restrict", 264, t["warn"], .12)]
    a.add(f'<line x1="{node_x}" y1="{node_y - 46}" x2="{node_x}" y2="{node_y + 46}" stroke="{a.t["fg"]}" stroke-width="1"/>')
    a.add(a.text(node_x, node_y - 54, "heedeo", "mono", 11, "fg", anchor="middle"))
    for i, (lbl, y, col, _) in enumerate(lanes):
        a.add(f'<rect x="478" y="{y - 10}" width="88" height="20" fill="{t["chip"]}" stroke="{t["line"]}"/>')
        a.add(a.text(522, y + 4, lbl, "mono", 11, col, anchor="middle"))
    for lbl, y, col, _ in lanes:
        a.add(f'<path d="M{node_x} {node_y} C{node_x + 50} {node_y} {node_x + 60} {y} 466 {y}" fill="none" stroke="{col}" stroke-opacity=".25"/>')
    n = 90
    dots = []
    for i in range(n):
        u = rnd.random()
        lane = lanes[0] if u < .68 else lanes[1] if u < .88 else lanes[2]
        y0 = node_y + rnd.uniform(-70, 70)
        x0 = 36 + rnd.uniform(0, 30)
        y_end = lane[1] + rnd.uniform(-3, 3)
        path = (f"M{x0:.0f} {y0:.0f} C{node_x - 140} {y0:.0f} {node_x - 60} {node_y} {node_x} {node_y} "
                f"C{node_x + 50} {node_y} {node_x + 60} {y_end:.0f} 466 {y_end:.0f}")
        dur = rnd.uniform(3.2, 4.4)
        begin = -rnd.uniform(0, dur)
        dots.append(f'<circle r="2" fill="{t["grey"]}"><animateMotion path="{path}" dur="{dur:.2f}s" begin="{begin:.2f}s" '
                    f'repeatCount="indefinite"/><animate attributeName="fill" values="{t["grey"]};{lane[2]}" keyTimes="0;1" '
                    f'calcMode="discrete" dur="{dur:.2f}s" begin="{begin + dur * .5:.2f}s" repeatCount="indefinite"/></circle>')
    a.add("".join(dots))


def v_voice(a):
    t = a.t
    n, x0, x1, ym = 54, 36, 564, 214
    w = (x1 - x0) / n
    out = []
    for i in range(n):
        env = .25 + .75 * math.sin(i / (n - 1) * math.pi) ** 1.5
        hs = [4 + 46 * env * abs(math.sin(i * .61 + k * 1.07)) for k in range(7)]
        hs.append(hs[0])
        out.append(f'<rect x="{x0 + i * w:.1f}" y="{ym - hs[0] / 2:.0f}" width="{w * .5:.1f}" height="{hs[0]:.0f}" fill="{t["acc"]}">'
                   f'<animate attributeName="height" values="{";".join(f"{h:.0f}" for h in hs)}" dur="1.6s" repeatCount="indefinite"/>'
                   f'<animate attributeName="y" values="{";".join(f"{ym - h / 2:.0f}" for h in hs)}" dur="1.6s" repeatCount="indefinite"/></rect>')
    a.add("".join(out))
    a.add(a.text(36, 268, "नमस्ते, म आर्जन हुँ।", "deva", 17, "fg"))
    a.add(a.text(564, 268, "TEXT → VOICE → TEXT", "mono", 11, "grey", .1, anchor="end"))


def v_papers(a):
    t = a.t
    pieces = ["न", "म", "स्", "ते"]
    y, h = 196, 40

    def chips(labels, x0, wchip, gap):
        out = []
        for i, s in enumerate(labels):
            x = x0 + i * (wchip + gap)
            out.append(f'<rect x="{x}" y="{y}" width="{wchip}" height="{h}" fill="{t["chip"]}" stroke="{t["line"]}"/>')
            out.append(a.text(x + wchip / 2, y + 27, s, "deva", 19, "fg", anchor="middle"))
        return "".join(out)

    split = chips(pieces, 36, 48, 8)
    whole = chips(["नमस्ते"], 36, 120, 0)
    period = 5
    a.add(f'<g>{split}<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.42;.5;.92;1" dur="{period}s" repeatCount="indefinite"/></g>')
    a.add(f'<g opacity="0">{whole}<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.42;.5;.92;1" dur="{period}s" repeatCount="indefinite"/></g>')
    a.add(f'<g>{a.text(300, 222, "4 tokens", "mono", 13, "grey")}'
          f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.42;.5;.92;1" dur="{period}s" repeatCount="indefinite"/></g>')
    a.add(f'<g opacity="0">{a.text(300, 222, "1 token", "mono", 13, "acc")}'
          f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.42;.5;.92;1" dur="{period}s" repeatCount="indefinite"/></g>')
    a.add(a.text(36, 268, "up to 5.8x more tokens for nepali, fixed to 1.01x", "geist", 15, "grey"))


def v_security(a):
    t = a.t
    names = ["google", "ea", "stanford", "shopify", "mit", "nba", "msi", "jetstar"]
    chips, x = [], 0
    for nm in names:
        s = f"+ {nm}"
        wch = width(s, "mono", 12) + 24
        chips.append(f'<rect x="{x:.0f}" y="0" width="{wch:.0f}" height="26" fill="{t["chip"]}" stroke="{t["line"]}"/>')
        chips.append(a.text(x + 12, 17, s, "mono", 12, "fg"))
        x += wch + 8
    total = x
    row = "".join(chips)
    cid = a.id("c")
    a.defs.append(f'<linearGradient id="{cid}g"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/>'
                  f'<stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="{cid}" maskUnits="userSpaceOnUse" x="36" y="180" width="528" height="40">'
                  f'<rect x="36" y="180" width="528" height="40" fill="url(#{cid}g)"/></mask>')
    a.add(f'<g mask="url(#{cid})"><g transform="translate(36 188)"><g>'
          f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{-total:.0f} 0" dur="{total / 40:.1f}s" repeatCount="indefinite"/>'
          f'{row}<g transform="translate({total:.0f} 0)">{row}</g></g></g></g>')
    a.add(a.text(36, 262, "cve-2025-51588", "mono", 13, "acc"))
    a.add(a.text(36 + width("cve-2025-51588", "mono", 13) + 12, 262, "assigned at 14", "geist", 15, "grey"))


CARDS = [
    ("heedeo", "FIG. 002 / COMPANY", "heedeo", "the trust layer for the agent economy.", "CO-FOUNDER & CTO  ·  EF F26", v_heedeo),
    ("voice", "FIG. 003 / MODELS", "swar & kriti", "the #1 nepali voice models.", "TTS + STT  ·  NAAMCHE LABS", v_voice),
    ("papers", "FIG. 004 / RESEARCH", "2 papers", "nepali tokenizers. ai pentesting agents.", "ARXIV 2026", v_papers),
    ("security", "FIG. 005 / SECURITY", "cve at 14", "100+ vulnerabilities in real companies.", "HACKERONE  ·  BUGCROWD  ·  JETSTAR HOF #2", v_security),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for th in THEMES:
        print(hero(th))
        for c in CARDS:
            print(card(th, *c))
