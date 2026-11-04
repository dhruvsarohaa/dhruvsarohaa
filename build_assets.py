"""Generates every SVG in assets/ from the PROFILE data below.

Edit PROFILE, then run:  python build_assets.py

The header's commit pane and the stats, languages and contribution cards read
live data from the GitHub API. They need a token in GITHUB_TOKEN, or a
logged-in `gh` CLI. Without one, those cards are left as they are.

Animations loop on purpose and ignore the "reduce motion" system setting, so
they play for every visitor. They only use opacity and transforms.
"""

import json
import os
import random
import subprocess
import urllib.request
from datetime import date
from pathlib import Path
from textwrap import wrap
from html import escape

PROFILE = {
    "username": "dhruvsarohaa",
    "name": "Dhruv Saroha",
    "role": "AI Engineer",
    "org": "KIET Group of Institutions",
    # The header types these commands and shows their output, in order.
    "now": "Building AutomateCLI",
    "status": "open to internships",
    "about": [
        ("role", "AI Engineer"),
        ("studies", "KIET Group of Institutions"),
        ("building", "AutomateCLI"),
        ("openTo", "Internships"),
        ("stack", ["TypeScript", "Python", "Flutter", "FastAPI"]),
    ],
    "featured": {
        "slug": "mediroutine",
        "title": "MediRoutine",
        "kind": "Android app",
        "desc": "Family medication companion: reminders, prescription scanning, "
                "family sync, SOS and an AI voice assistant.",
        "tags": ["Flutter", "FastAPI", "Firebase"],
        "figure": ("10", "Indian languages in the voice assistant"),
    },
    "projects": [
        {
            "slug": "axar",
            "title": "axar",
            "kind": "Library",
            "desc": "A minimal TypeScript agent framework that stays simple and keeps you in control.",
            "tags": ["TypeScript", "Agents"],
        },
        {
            "slug": "medalert",
            "title": "MedAlert for iOS",
            "kind": "iOS app",
            "desc": "Native iOS port of the MedAlert medication reminder app.",
            "tags": ["SwiftUI", "SwiftData"],
        },
        {
            "slug": "automatecli",
            "title": "AutomateCLI",
            "kind": "In progress",
            "desc": "What I'm building now. Details soon.",
            "tags": ["CLI"],
        },
    ],
    "sections": [("about", "about"), ("selected-work", "work"), ("toolkit", "toolkit"), ("activity", "activity")],
    "buttons": [
        ("portfolio", "Portfolio", "globe", True),
        ("linkedin", "LinkedIn", "linkedin", False),
        ("email", "Email", "mail", False),
    ],
    "site": "dhruvsaroha.space",
}

# Ink surfaces tinted toward violet, violet as the accent and the light source.
SPACE = "#07060C"
CARD = "#0F0E17"
RAISED = "#1A1826"
TEXT = "#F1EFFA"
SECOND = "#A9A5BF"
MUTED = "#7F7A96"
ACCENT = "#9D7CFF"
DEEP = "#5B3FD9"
GLOW = "#C4B5FD"
POSITIVE = "#4CC38A"
HAIR = f'stroke="{TEXT}" stroke-opacity=".09"'

LIGHT = {"text": "#14141C", "muted": "#6B6B80", "accent": "#6A47E0"}

SANS = "-apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', 'Cascadia Code', Consolas, 'Liberation Mono', monospace"

EASE = "cubic-bezier(.22, 1, .36, 1)"
RISE = f".rise {{ opacity: 0; animation: rise .6s {EASE} forwards; }} @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}"

OUT = Path(__file__).parent / "assets"


def svg(w, h, label, body, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">\n'
        f"<style>{style}</style>\n{body}\n</svg>\n"
    )


def text_width(s, size, mono=False):
    return len(s) * size * (0.6 if mono else 0.54)


# Shared pieces -------------------------------------------------------------

def beam(uid, x, y, w, h, r, dur=7, delay=0):
    """A short streak of light that travels around a rounded rectangle's edge."""
    perim = 2 * (w + h) - (8 - 2 * 3.1416) * r
    seg = min(220, perim * .12)
    return f"""
  <linearGradient id="bm-{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{GLOW}"/><stop offset=".5" stop-color="{ACCENT}"/><stop offset="1" stop-color="#FFFFFF"/></linearGradient>
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="url(#bm-{uid})" stroke-width="1.5" stroke-linecap="round"
        stroke-dasharray="{seg:.0f} {perim - seg:.0f}" opacity=".9">
    <animate attributeName="stroke-dashoffset" from="0" to="{-perim:.0f}" dur="{dur}s" begin="{delay}s" repeatCount="indefinite"/>
  </rect>"""


def card_base(uid, w, h, r=18, light=("12%", "0%")):
    """Raised surface with a soft light in one corner, a lit top edge and a hairline."""
    return f"""
  <defs>
    <radialGradient id="lt-{uid}" cx="{light[0]}" cy="{light[1]}" r="75%"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".16"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>
    <linearGradient id="edge-{uid}" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  </defs>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{CARD}" {HAIR}/>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="url(#lt-{uid})"/>
  <path d="M{r} .75H{w - r}" stroke="url(#edge-{uid})" stroke-width="1"/>"""


def sweep_text(uid, x, y, content, attrs, dur=5, delay=0, base=None):
    """Silver text with a band of light passing over it."""
    base = base or f"url(#sv-{uid})"
    return f"""
  <defs>
    <linearGradient id="sv-{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".7" stop-color="#DCD6F5"/><stop offset="1" stop-color="#A99FD6"/></linearGradient>
    <linearGradient id="sw-{uid}" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="{x - 100} 0;{x + 1100} 0" keyTimes="0;1" dur="{dur}s" begin="{delay}s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <text x="{x}" y="{y}" {attrs} fill="{base}">{content}</text>
  <text x="{x}" y="{y}" {attrs} fill="url(#sw-{uid})" opacity=".55">{content}</text>"""


# Header --------------------------------------------------------------------

def recent_commits(user, n=5):
    commits = []
    for repo in user["recent"]["nodes"]:
        if repo["name"].lower() == PROFILE["username"].lower():
            continue  # skip this README repo and its bot refreshes
        ref = repo["defaultBranchRef"]
        for c in (ref["target"]["history"]["nodes"] if ref else []):
            commits.append((c["committedDate"], c["abbreviatedOid"], repo["name"], c["messageHeadline"]))
    seen, distinct = set(), []
    for commit in sorted(commits, reverse=True):
        if commit[3].lower() not in seen:
            seen.add(commit[3].lower())
            distinct.append(commit)
    return distinct[:n]


def header(user=None):
    """A terminal floating over a violet horizon. It types three commands, prints
    their output, lists the latest commits in a second pane, then loops."""
    W, H = 1200, 620
    T = 16.0  # seconds per loop
    wx, wy, ww, wh = 110, 64, 980, 448  # terminal window
    size, cw = 17, 17 * 0.6
    lx = wx + 44
    rx = wx + ww * .53 + 36
    parts, keyframes = [], []

    def pct(t):
        return min(99.0, t / T * 100)

    def command(y, cmd, start, x0):
        n = len(cmd)
        end = start + n * .075
        cmd_x = x0 + 2 * cw
        d = n * cw
        i = len(keyframes)
        keyframes.append(
            f"@keyframes cv{i} {{ 0%, {pct(start):.2f}% {{ transform: translateX(0); animation-timing-function: steps({n}, end); }} {pct(end):.2f}%, 100% {{ transform: translateX({d:.1f}px); }} }}"
            f" @keyframes on{i} {{ 0%, {pct(start):.2f}% {{ opacity: 0; }} {pct(start) + .01:.2f}%, {pct(end):.2f}% {{ opacity: 1; }} {pct(end) + .01:.2f}%, 100% {{ opacity: 0; }} }}"
            f" .cv{i} {{ animation: cv{i} {T}s infinite; }} .ty{i} {{ animation: cv{i} {T}s infinite, on{i} {T}s infinite; }}"
        )
        parts.append(
            f'  <text x="{x0}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{ACCENT}">&gt;</text>'
            f'<text x="{cmd_x:.1f}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{TEXT}">{escape(cmd)}</text>'
            f'<rect class="cv{i}" x="{cmd_x - 2:.1f}" y="{y - 19}" width="{d + 26:.0f}" height="26" fill="{CARD}"/>'
            f'<rect class="ty{i}" x="{cmd_x:.1f}" y="{y - 15}" width="9" height="20" fill="{ACCENT}"/>'
        )
        return end

    def output(markup, start):
        i = len(keyframes)
        s = pct(start)
        keyframes.append(
            f"@keyframes o{i} {{ 0%, {s:.2f}% {{ opacity: 0; transform: translateY(10px); }} {min(99.5, s + 4):.2f}%, 100% {{ opacity: 1; transform: none; }} }}"
            f" .o{i} {{ animation: o{i} {T}s {EASE} infinite; }}"
        )
        parts.append(f'  <g class="o{i}">{markup}</g>')

    p = PROFILE
    t = command(wy + 92, "whoami", .8, lx)
    output(sweep_text("name", lx - 3, wy + 160, escape(p["name"]),
                      f'font-family="{SANS}" font-size="58" font-weight="600" letter-spacing="-1.8"', dur=4.5, delay=2), t + .2)
    output(f'<text x="{lx}" y="{wy + 196}" font-family="{SANS}" font-size="18" fill="{SECOND}">{escape(p["role"])}  ·  {escape(p["org"])}</text>', t + .35)
    t = command(wy + 252, "cat now.txt", t + 1.2, lx)
    output(f'<text x="{lx}" y="{wy + 284}" font-family="{MONO}" font-size="{size}" fill="{TEXT}">{escape(p["now"])}</text>', t + .2)
    t = command(wy + 336, "status", t + .8, lx)
    output(
        f'<circle cx="{lx + 5}" cy="{wy + 362}" r="5" fill="{POSITIVE}"><animate attributeName="opacity" values="1;.4;1" dur="2s" repeatCount="indefinite"/></circle>'
        f'<text x="{lx + 20}" y="{wy + 368}" font-family="{MONO}" font-size="{size}" fill="{TEXT}">{escape(p["status"])}</text>',
        t + .2,
    )
    output(
        f'<text x="{lx}" y="{wy + 412}" font-family="{MONO}" font-size="{size}" fill="{ACCENT}">&gt;</text>'
        f'<rect x="{lx + 2 * cw:.1f}" y="{wy + 397}" width="9" height="20" fill="{ACCENT}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>',
        t + .6,
    )

    commits = recent_commits(user) if user else []
    if commits:
        parts.append(f'  <path d="M{wx + ww * .53:.0f} {wy + 45}V{wy + wh - 1}" {HAIR}/>')
        ct = command(wy + 92, "git log --oneline", 2.4, rx)
        for i, (_, sha, repo, msg) in enumerate(commits):
            y = wy + 144 + i * 56
            msg = msg if len(msg) <= 30 else msg[:29].rstrip() + "…"
            output(
                f'<text x="{rx}" y="{y}" font-family="{MONO}" font-size="15" fill="{ACCENT}" fill-opacity=".8">{escape(sha)}'
                f'<tspan dx="10" fill="{TEXT}" fill-opacity="1">{escape(msg)}</tspan></text>'
                f'<text x="{rx + 7 * 9 + 10:.0f}" y="{y + 21}" font-family="{MONO}" font-size="12.5" fill="{MUTED}">{escape(repo)}</text>',
                ct + .2 + i * .12,
            )

    rnd = random.Random(7)
    stars = "".join(
        f'<circle cx="{rnd.uniform(10, W - 10):.0f}" cy="{rnd.uniform(10, 420):.0f}" r="{rnd.choice([.7, .9, 1.2, 1.5])}" fill="#fff">'
        f'<animate attributeName="opacity" values=".1;{rnd.uniform(.5, .9):.2f};.1" dur="{rnd.uniform(2.5, 6):.1f}s" begin="{rnd.uniform(0, 4):.1f}s" repeatCount="indefinite"/></circle>'
        for _ in range(60)
    )

    body = f"""
  <defs>
    <clipPath id="clip"><rect width="{W}" height="{H}" rx="24"/></clipPath>
    <radialGradient id="horizon" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{GLOW}" stop-opacity=".9"/><stop offset=".3" stop-color="{ACCENT}" stop-opacity=".6"/><stop offset=".6" stop-color="{DEEP}" stop-opacity=".25"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rim" x1="0" x2="1"><stop offset="0" stop-color="{GLOW}" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></linearGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GLOW}" stop-opacity=".22"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></linearGradient>
    <filter id="haze" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="30" stdDeviation="30" flood-color="#000" flood-opacity=".7"/></filter>
    <linearGradient id="topedge" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  </defs>
  <g clip-path="url(#clip)">
    <rect width="{W}" height="{H}" fill="{SPACE}"/>
    <polygon points="540,-40 660,-40 980,{H} 220,{H}" fill="url(#beam)" filter="url(#haze)">
      <animate attributeName="opacity" values=".6;1;.6" dur="8s" repeatCount="indefinite"/>
    </polygon>
    {stars}
    <ellipse cx="600" cy="{H + 10}" rx="760" ry="240" fill="url(#horizon)">
      <animate attributeName="ry" values="240;275;240" dur="9s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="600" cy="{H + 210}" rx="760" ry="250" fill="none" stroke="url(#rim)" stroke-width="5" filter="url(#soft)" opacity=".8">
      <animate attributeName="opacity" values=".55;.95;.55" dur="6s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="600" cy="{H + 210}" rx="760" ry="250" fill="none" stroke="url(#rim)" stroke-width="1.2"/>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" {HAIR}/>

  <g filter="url(#shadow)"><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="16" fill="{CARD}" fill-opacity=".94"/></g>
  <rect x="{wx + .5}" y="{wy + .5}" width="{ww - 1}" height="{wh - 1}" rx="16" fill="none" stroke="{TEXT}" stroke-opacity=".12"/>
  <path d="M{wx + 16} {wy + .75}H{wx + ww - 16}" stroke="url(#topedge)"/>
  {beam("win", wx + .5, wy + .5, ww - 1, wh - 1, 16, dur=9)}
  <path d="M{wx + 1} {wy + 44}H{wx + ww - 1}" {HAIR}/>
  <circle cx="{wx + 24}" cy="{wy + 22}" r="6" fill="#FF5F57" fill-opacity=".85"/><circle cx="{wx + 44}" cy="{wy + 22}" r="6" fill="#FEBC2E" fill-opacity=".85"/><circle cx="{wx + 64}" cy="{wy + 22}" r="6" fill="#28C840" fill-opacity=".85"/>
  <text x="{wx + ww / 2:.0f}" y="{wy + 27}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(p["username"])} — zsh</text>
  <g class="loop">
{chr(10).join(parts)}
  </g>"""
    style = (
        "\n".join(keyframes)
        + f"\n.loop {{ animation: loop {T}s infinite; }} @keyframes loop {{ 0%, 95% {{ opacity: 1; }} 98.5%, 100% {{ opacity: 0; }} }}"
    )
    return svg(W, H, f'{p["name"]}, {p["role"]} at {p["org"]}. {p["now"]}, {p["status"]}.', body, style)


# Small pieces --------------------------------------------------------------

def footer():
    w, h = 1200, 160
    body = f"""
  <defs>
    <clipPath id="c"><rect width="{w}" height="{h}" rx="20"/></clipPath>
    <radialGradient id="hz" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{GLOW}" stop-opacity=".8"/><stop offset=".35" stop-color="{ACCENT}" stop-opacity=".45"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0"/></radialGradient>
    <linearGradient id="rim" x1="0" x2="1"><stop offset="0" stop-color="{GLOW}" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></linearGradient>
  </defs>
  <g clip-path="url(#c)">
    <rect width="{w}" height="{h}" fill="{SPACE}"/>
    <ellipse cx="600" cy="{h + 20}" rx="640" ry="110" fill="url(#hz)"><animate attributeName="ry" values="110;130;110" dur="8s" repeatCount="indefinite"/></ellipse>
    <ellipse cx="600" cy="{h + 120}" rx="640" ry="150" fill="none" stroke="url(#rim)" stroke-width="1.2" opacity=".8"/>
  </g>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="none" {HAIR}/>
  <text x="48" y="74" font-family="{MONO}" font-size="17" fill="{ACCENT}">&gt;<tspan fill="{SECOND}" dx="10">exit</tspan></text>
  <rect x="{48 + 7 * 10.2:.0f}" y="60" width="9" height="19" fill="{ACCENT}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>
  <text x="{w - 48}" y="74" text-anchor="end" font-family="{MONO}" font-size="16" fill="{SECOND}">{escape(PROFILE["site"])}</text>"""
    return svg(w, h, PROFILE["site"], body)


def section(title, theme):
    w, h = 1200, 72
    c = {"dark": {"text": TEXT, "accent": ACCENT}, "light": LIGHT}[theme]
    label = f"~/{title}"
    line_x = text_width(label, 22, mono=True) + 24
    span = w - line_x
    body = f"""
  <defs><linearGradient id="dot" x1="0" x2="1"><stop offset="0" stop-color="{c["accent"]}" stop-opacity="0"/><stop offset="1" stop-color="{c["accent"]}"/></linearGradient></defs>
  <text x="0" y="44" font-family="{MONO}" font-size="22" fill="{c["text"]}"><tspan fill="{c["accent"]}">~/</tspan>{escape(title)}</text>
  <rect x="{line_x:.0f}" y="37" width="{span:.0f}" height="1" fill="{c["text"]}" fill-opacity=".12"/>
  <rect x="{line_x:.0f}" y="36" width="160" height="3" rx="1.5" fill="url(#dot)">
    <animate attributeName="x" values="{line_x - 160:.0f};{w:.0f}" dur="5s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="5s" repeatCount="indefinite"/>
  </rect>"""
    return svg(w, h, title, body)


def code_card():
    w = 1200
    rows = [[("kw", "const "), ("v", "dhruv"), ("p", " = {")]]
    for key, value in PROFILE["about"]:
        if isinstance(value, list):
            parts = [("p", "[")]
            for i, item in enumerate(value):
                parts += [("s", f'"{item}"')] + ([("p", ", ")] if i < len(value) - 1 else [])
            parts += [("p", "],")]
        else:
            parts = [("s", f'"{value}"'), ("p", ",")]
        rows.append([("p", "  "), ("k", key.ljust(10)), ("p", ": ")] + parts)
    rows.append([("p", "};")])

    colors = {"kw": ACCENT, "v": TEXT, "p": MUTED, "k": GLOW, "s": "#E9E4FF"}
    top, lh = 100, 34
    h = top + lh * (len(rows) - 1) + 44
    T = 12
    lines, kf = [], []
    for i, row in enumerate(rows):
        spans = "".join(f'<tspan fill="{colors[k]}">{escape(t)}</tspan>' for k, t in row)
        y = top + i * lh
        s = (.3 + i * .12) / T * 100
        kf.append(f"@keyframes l{i} {{ 0%, {s:.1f}% {{ opacity: 0; transform: translateX(-8px); }} {s + 4:.1f}%, 94% {{ opacity: 1; transform: none; }} 98%, 100% {{ opacity: 0; }} }} .l{i} {{ animation: l{i} {T}s {EASE} infinite; }}")
        lines.append(
            f'  <g class="l{i}"><text x="56" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{MUTED}" fill-opacity=".6">{i + 1}</text>'
            f'<text x="80" y="{y}" font-family="{MONO}" font-size="18" xml:space="preserve">{spans}</text></g>'
        )
    body = f"""{card_base("ab", w, h, light=("100%", "0%"))}
  {beam("ab", .5, .5, w - 1, h - 1, 18, dur=10)}
  <path d="M1 48H{w - 1}" {HAIR}/>
  <circle cx="26" cy="24" r="5.5" fill="{TEXT}" fill-opacity=".15"/><circle cx="44" cy="24" r="5.5" fill="{TEXT}" fill-opacity=".15"/><circle cx="62" cy="24" r="5.5" fill="{TEXT}" fill-opacity=".15"/>
  <text x="{w / 2:.0f}" y="29" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">about.ts</text>
{chr(10).join(lines)}"""
    return svg(w, h, "About Dhruv: " + ", ".join(f"{k} {v}" for k, v in PROFILE["about"] if not isinstance(v, list)), body, "\n".join(kf))


def arrow(x, y, color=MUTED):
    return f'<path d="M{x} {y + 12} L{x + 12} {y} M{x + 3} {y} H{x + 12} V{y + 9}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'


def featured_card():
    p = PROFILE["featured"]
    w, h = 1200, 280
    desc = wrap(p["desc"], 52)[:3]
    desc_svg = "".join(
        f'<text x="44" y="{142 + j * 28}" font-family="{SANS}" font-size="18" fill="{SECOND}">{escape(line)}</text>' for j, line in enumerate(desc)
    )
    figure, caption = p["figure"]
    body = f"""{card_base("ft", w, h, light=("85%", "30%"))}
  {beam("ft", .5, .5, w - 1, h - 1, 18, dur=8)}
  <g class="rise">
    <text x="44" y="62" font-family="{MONO}" font-size="13" fill="{ACCENT}">{escape(p["kind"])}</text>
    <text x="44" y="104" font-family="{SANS}" font-size="34" font-weight="600" letter-spacing="-.8" fill="{TEXT}">{escape(p["title"])}</text>
    {desc_svg}
    <text x="44" y="{h - 40}" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape("  ·  ".join(p["tags"]))}</text>
  </g>
  <path d="M760 44V{h - 44}" {HAIR}/>
  {sweep_text("fig", 800, 168, escape(figure), f'font-family="{SANS}" font-size="112" font-weight="600" letter-spacing="-4"', dur=5, delay=1)}
  <text x="804" y="208" font-family="{SANS}" font-size="16" fill="{SECOND}">{escape(caption)}</text>
  {arrow(w - 56, 44, SECOND)}"""
    return svg(w, h, f'{p["title"]}: {p["desc"]}', body, RISE)


def project_card(p, i):
    w, h = 392, 240
    desc = wrap(p["desc"], 38)[:3]
    desc_svg = "".join(
        f'<text x="28" y="{124 + j * 24}" font-family="{SANS}" font-size="15.5" fill="{SECOND}">{escape(line)}</text>' for j, line in enumerate(desc)
    )
    body = f"""{card_base(f"p{i}", w, h, light=("0%", "0%"))}
  {beam(f"p{i}", .5, .5, w - 1, h - 1, 18, dur=7, delay=i * 2.3)}
  <g class="rise" style="animation-delay:{.1 + i * .08:.2f}s">
    <text x="28" y="50" font-family="{MONO}" font-size="13" fill="{ACCENT}">{escape(p["kind"])}</text>
    <text x="28" y="88" font-family="{SANS}" font-size="23" font-weight="600" letter-spacing="-.4" fill="{TEXT}">{escape(p["title"])}</text>
    {desc_svg}
    <text x="28" y="{h - 28}" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape("  ·  ".join(p["tags"]))}</text>
  </g>
  {arrow(w - 44, 36, SECOND)}"""
    return svg(w, h, f'{p["title"]}: {p["desc"]}', body, RISE)


def icon(name, color):
    return {
        "globe": f'<circle r="8" fill="none" stroke="{color}" stroke-width="1.6"/><ellipse rx="3.5" ry="8" fill="none" stroke="{color}" stroke-width="1.6"/><path d="M-8 0H8" stroke="{color}" stroke-width="1.6"/>',
        "linkedin": f'<rect x="-8" y="-8" width="16" height="16" rx="3" fill="none" stroke="{color}" stroke-width="1.6"/><path d="M-4 -1V4.5M-4 -4.2V-4M0 4.5V-1M0 1.5C0 -.5 4 -1.5 4 1.5V4.5" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>',
        "mail": f'<rect x="-8.5" y="-6.5" width="17" height="13" rx="2.5" fill="none" stroke="{color}" stroke-width="1.6"/><path d="M-7.5 -5 L0 1 L7.5 -5" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round"/>',
    }[name]


def button(label, name, primary):
    w, h = 176, 52
    if primary:
        body = f"""
  <defs>
    <linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B49BFF"/><stop offset="1" stop-color="#7A5AF0"/></linearGradient>
    <linearGradient id="sh" gradientUnits="userSpaceOnUse" x1="-80" y1="0" x2="0" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-20 0;300 0;300 0" keyTimes="0;.35;1" dur="4s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="12" fill="url(#f)"/>
  <rect width="{w}" height="{h}" rx="12" fill="url(#sh)"/>
  <path d="M12 1H{w - 12}" stroke="#fff" stroke-opacity=".5"/>
  <g transform="translate(30 26)">{icon(name, "#120E22")}</g>
  <text x="52" y="31.5" font-family="{SANS}" font-size="16" font-weight="600" fill="#120E22">{escape(label)}</text>
  {arrow(w - 34, 20, "#120E22")}"""
    else:
        body = f"""
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{RAISED}" stroke="{TEXT}" stroke-opacity=".12"/>
  <path d="M12 1.5H{w - 12}" stroke="#fff" stroke-opacity=".14"/>
  <g transform="translate(30 26)">{icon(name, GLOW)}</g>
  <text x="52" y="31.5" font-family="{SANS}" font-size="16" font-weight="500" fill="{TEXT}">{escape(label)}</text>
  {arrow(w - 34, 20)}"""
    return svg(w, h, label, body)


# GitHub data ---------------------------------------------------------------

QUERY = """
query($login: String!) {
  user(login: $login) {
    recent: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 7, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        defaultBranchRef { target { ... on Commit { history(first: 15) { nodes { abbreviatedOid messageHeadline committedDate } } } } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}"""


def github_token():
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def fetch_github():
    token = github_token()
    if not token:
        return None
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": PROFILE["username"]}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.load(res)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]


def days_of(user):
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [d for wk in weeks for d in wk["contributionDays"]]


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    # Today may still be empty without breaking the current streak.
    recent = days[:-1] if days and not days[-1]["contributionCount"] else days
    current = 0
    for d in reversed(recent):
        if not d["contributionCount"]:
            break
        current += 1
    return current, longest


def card_head(w, title, meta):
    return (
        f'  <text x="32" y="54" font-family="{SANS}" font-size="17" font-weight="600" fill="{TEXT}">{escape(title)}</text>'
        f'<text x="{w - 32}" y="54" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(meta)}</text>'
    )


def odometer(uid, x, y, value, size, color, delay, T=12):
    """Digits roll up from 0 like an odometer, hold, and roll again each loop."""
    lh = size * 1.2
    dw = size * .58
    out, kf = [f'<clipPath id="od-{uid}"><rect x="{x - 4}" y="{y - size * .95:.1f}" width="{len(value) * dw + 12:.0f}" height="{lh:.1f}"/></clipPath><g clip-path="url(#od-{uid})">'], []
    for j, ch in enumerate(value):
        cx = x + j * dw
        if not ch.isdigit():
            out.append(f'<text x="{cx:.1f}" y="{y}" font-family="{SANS}" font-size="{size}" font-weight="600" fill="{color}">{escape(ch)}</text>')
            continue
        d = int(ch) + 10  # roll through one full turn before landing
        s = (delay + j * .08) / T * 100
        e = s + 14
        name = f"r{uid}{j}"
        kf.append(
            f"@keyframes {name} {{ 0%, {s:.1f}% {{ transform: translateY(0); animation-timing-function: cubic-bezier(.16,1,.3,1); }} {e:.1f}%, 100% {{ transform: translateY({-d * lh:.1f}px); }} }}"
            f" .{name} {{ animation: {name} {T}s infinite; }}"
        )
        digits = "".join(
            f'<text x="{cx:.1f}" y="{y + k * lh:.1f}" font-family="{SANS}" font-size="{size}" font-weight="600" fill="{color}">{k % 10}</text>' for k in range(d + 1)
        )
        out.append(f'<g class="{name}">{digits}</g>')
    out.append("</g>")
    return "".join(out), kf


def stats_card(user):
    w, h = 708, 300
    days = days_of(user)
    current, longest = streaks(days)
    cc = user["contributionsCollection"]
    items = [
        ("Contributions", f'{cc["contributionCalendar"]["totalContributions"]:,}'),
        ("Commits", f'{cc["totalCommitContributions"]:,}'),
        ("Active days", str(sum(1 for d in days if d["contributionCount"]))),
        ("Longest streak", f"{longest}d"),
        ("Current streak", f"{current}d"),
        ("Public repos", str(user["repositories"]["totalCount"])),
    ]
    cells, kfs = [], []
    for i, (label, value) in enumerate(items):
        x, y = 32 + (i % 3) * 220, 136 + (i // 3) * 104
        markup, kf = odometer(i, x, y, value, 34, ACCENT if i == 0 else TEXT, .3 + i * .1)
        kfs += kf
        cells.append(f'  {markup}<text x="{x}" y="{y + 30}" font-family="{SANS}" font-size="14" fill="{SECOND}">{label}</text>')
    body = f"{card_base('st', w, h)}\n{beam('st', .5, .5, w - 1, h - 1, 18, dur=9)}\n{card_head(w, 'GitHub', 'last 12 months')}\n" + "\n".join(cells)
    return svg(w, h, "GitHub stats for the last 12 months: " + ", ".join(f"{l} {v}" for l, v in items), body, "\n".join(kfs))


def languages_card(user):
    w, h = 472, 300
    sizes = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] = sizes.get(edge["node"]["name"], 0) + edge["size"]
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    lead = top[0][1] if top else 1
    rows = []
    for i, (name, size) in enumerate(top):
        y = 106 + i * 40
        bar_w = (w - 64) * size / lead
        rows.append(
            f'  <text x="32" y="{y}" font-family="{SANS}" font-size="15" fill="{TEXT}">{escape(name)}</text>'
            f'<text x="{w - 32}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUTED}">{size / total:.0%}</text>'
            f'<rect x="32" y="{y + 10}" width="{w - 64}" height="5" rx="2.5" fill="{TEXT}" fill-opacity=".07"/>'
            f'<rect class="bar" style="animation-delay:{.2 + i * .08:.2f}s" x="32" y="{y + 10}" width="{bar_w:.1f}" height="5" rx="2.5" fill="{"url(#lead)" if i == 0 else SECOND}" fill-opacity="{1 if i == 0 else .5}"/>'
        )
    body = f"""{card_base("lg", w, h, light=("100%", "0%"))}
  <defs><linearGradient id="lead" gradientUnits="userSpaceOnUse" x1="0" x2="{w}"><stop offset="0" stop-color="{DEEP}"/><stop offset=".5" stop-color="{GLOW}"/><stop offset="1" stop-color="{ACCENT}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-{w} 0;{w} 0" dur="3s" repeatCount="indefinite"/></linearGradient></defs>
  {beam("lg", .5, .5, w - 1, h - 1, 18, dur=9, delay=4)}
{card_head(w, "Languages", "by code size")}
""" + "\n".join(rows)
    style = f".bar {{ transform-origin: 32px 0; animation: bar 12s {EASE} infinite; }} @keyframes bar {{ 0% {{ transform: scaleX(0); }} 12%, 100% {{ transform: scaleX(1); }} }}"
    return svg(w, h, "Most used languages: " + ", ".join(n for n, _ in top), body, style)


def contributions_card(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"][-53:]
    step, cell = 20.4, 16
    w = 1200
    gx, gy = (w - (len(weeks) - 1) * step - cell) / 2, 104
    h = int(gy + 7 * step + 56)
    peak = max((d["contributionCount"] for wk in weeks for d in wk["contributionDays"]), default=0) or 1
    scale = ["#1C1A28", "#33295E", "#5040A0", "#7D5FE6", "#C4B2FF"]

    def level(n):
        return 0 if n == 0 else min(4, 1 + int(3.999 * n / peak))

    cells, mask, months, last_month = [], [], [], None
    for wi, wk in enumerate(weeks):
        x = gx + wi * step
        for d in wk["contributionDays"]:
            day = date.fromisoformat(d["date"])
            y = gy + ((day.weekday() + 1) % 7) * step
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="4" fill="{scale[level(d["contributionCount"])]}"/>')
            if d["contributionCount"]:
                mask.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="4" fill="#fff"/>')
        first = date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                months.append(f'<text x="{x:.1f}" y="{gy - 14}" font-family="{MONO}" font-size="12" fill="{MUTED}">{first.strftime("%b")}</text>')
            last_month = first.month

    ly = h - 28
    legend = "".join(f'<rect x="{w - 168 + i * 20}" y="{ly - 12}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(scale))
    body = (
        card_base("ct", w, h, light=("50%", "0%"))
        + f"""
  <defs>
    <mask id="active">{"".join(mask)}</mask>
    <linearGradient id="wave" gradientUnits="userSpaceOnUse" x1="-240" x2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".6" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;{w + 240} 0;{w + 240} 0" keyTimes="0;.6;1" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  {beam("ct", .5, .5, w - 1, h - 1, 18, dur=12)}
{card_head(w, "Contributions", "")}<text x="{w - 32}" y="54" text-anchor="end" font-family="{SANS}" font-size="17" fill="{SECOND}"><tspan fill="{TEXT}" font-weight="600">{cal["totalContributions"]:,}</tspan> in the last year</text>
  {"".join(months)}
  <g class="grid">{"".join(cells)}</g>
  <rect x="0" y="{gy}" width="{w}" height="{7 * step}" fill="url(#wave)" mask="url(#active)"/>
  <text x="{w - 180}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">less</text>{legend}<text x="{w - 64}" y="{ly}" font-family="{MONO}" font-size="12" fill="{MUTED}">more</text>"""
    )
    style = f".grid {{ animation: in .8s {EASE} both; }} @keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} }}"
    return svg(w, h, f'{cal["totalContributions"]} contributions in the last year', body, style)


def main():
    OUT.mkdir(exist_ok=True)
    files = {"about.svg": code_card(), "footer.svg": footer(), "project-" + PROFILE["featured"]["slug"] + ".svg": featured_card()}
    for theme in ("dark", "light"):
        for slug, title in PROFILE["sections"]:
            files[f"section-{slug}-{theme}.svg"] = section(title, theme)
    for i, project in enumerate(PROFILE["projects"]):
        files[f'project-{project["slug"]}.svg'] = project_card(project, i)
    for slug, label, name, primary in PROFILE["buttons"]:
        files[f"button-{slug}.svg"] = button(label, name, primary)

    try:
        user = fetch_github()
    except Exception as err:  # keep the last good cards if the API call fails
        print(f"GitHub API failed, keeping existing data cards: {err}")
        user = None
    if user:
        files["header.svg"] = header(user)
        files["stats.svg"] = stats_card(user)
        files["languages.svg"] = languages_card(user)
        files["contributions.svg"] = contributions_card(user)
    elif not (OUT / "header.svg").exists():
        files["header.svg"] = header()

    for old in ("footer-dark.svg", "footer-light.svg"):
        (OUT / old).unlink(missing_ok=True)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(f"Wrote {len(files)} files to {OUT}")


if __name__ == "__main__":
    main()
