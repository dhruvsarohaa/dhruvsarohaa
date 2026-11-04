"""Generates every SVG in assets/ from the PROFILE data below.

Edit PROFILE, then run:  python build_assets.py

The stats, languages and contribution cards read live data from the GitHub API.
They need a token in GITHUB_TOKEN, or a logged-in `gh` CLI. Without one, those
three cards are left as they are and everything else is still rebuilt.
"""

import json
import os
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
        ("portfolio", "Portfolio", "globe"),
        ("linkedin", "LinkedIn", "linkedin"),
        ("email", "Email", "mail"),
    ],
    "site": "dhruvsaroha.space",
}

# One ink ramp, tinted a little toward violet, and violet as the only accent.
DEEP = "#0A0A10"
CARD = "#121219"
RAISED = "#1A1A23"
TEXT = "#EEEEF6"
SECOND = "#A6A6B8"
MUTED = "#7E7E92"
ACCENT = "#9D7CFF"
POSITIVE = "#4CC38A"
HAIR = f'stroke="{TEXT}" stroke-opacity=".08"'

LIGHT = {"text": "#14141C", "muted": "#6B6B80", "accent": "#6A47E0"}

SANS = "-apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', 'Cascadia Code', Consolas, 'Liberation Mono', monospace"
NUM = "font-variant-numeric: tabular-nums;"

EASE = "cubic-bezier(.22, 1, .36, 1)"
RISE = f".rise {{ opacity: 0; animation: rise .45s {EASE} forwards; }} @keyframes rise {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}"
REDUCED = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } .rise, .ln, .c, .bar { opacity: 1 !important; } .bar { transform: none !important; } .cover, .typing { display: none; } }"

OUT = Path(__file__).parent / "assets"


def svg(w, h, label, body, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">\n'
        f"<style>{style}\n{REDUCED}</style>\n{body}\n</svg>\n"
    )


def frame(w, h, r=16, fill=CARD):
    return f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{fill}" {HAIR}/>'


def text_width(s, size, mono=False):
    return len(s) * size * (0.6 if mono else 0.54)


def recent_commits(user, n=5):
    commits = []
    for repo in user["recent"]["nodes"]:
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
    """A terminal that types three commands and prints their output.

    With GitHub data, a second pane on the right lists the latest public commits.
    """
    w, h = 1200, 480
    p = PROFILE
    size, cw, x0 = 18, 18 * 0.6, 48
    parts, styles = [], []

    def command(y, cmd, start, x0=x0):
        dur = len(cmd) * .07
        cmd_x = x0 + 2 * cw
        cover_w = len(cmd) * cw + 24
        i = len(styles)
        styles.append(
            f".cv{i} {{ animation: type{i} {dur:.2f}s steps({len(cmd)}) {start:.2f}s forwards; }}"
            f" .ty{i} {{ opacity: 0; animation: type{i} {dur:.2f}s steps({len(cmd)}) {start:.2f}s forwards, on {dur:.2f}s steps(1) {start:.2f}s; }}"
            f" @keyframes type{i} {{ to {{ transform: translateX({len(cmd) * cw:.1f}px); }} }}"
        )
        parts.append(
            f'  <text x="{x0}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{ACCENT}">&gt;</text>'
            f'<text x="{cmd_x:.1f}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{TEXT}">{escape(cmd)}</text>'
            f'<rect class="cover cv{i}" x="{cmd_x - 2:.1f}" y="{y - 20}" width="{cover_w:.0f}" height="28" fill="{CARD}"/>'
            f'<rect class="typing ty{i}" x="{cmd_x:.1f}" y="{y - 16}" width="10" height="21" fill="{ACCENT}"/>'
        )
        return start + dur

    def output(markup, start):
        parts.append(f'  <g class="rise" style="animation-delay:{start:.2f}s">{markup}</g>')

    t = command(104, "whoami", .4)
    output(
        f'<text x="{x0 - 3}" y="178" font-family="{SANS}" font-size="64" font-weight="500" letter-spacing="-1.9" fill="{TEXT}">{escape(p["name"])}</text>',
        t + .15,
    )
    output(
        f'<text x="{x0}" y="216" font-family="{SANS}" font-size="20" fill="{SECOND}">{escape(p["role"])}  ·  {escape(p["org"])}</text>',
        t + .25,
    )
    t = command(276, "cat now.txt", t + .9)
    output(f'<text x="{x0}" y="310" font-family="{MONO}" font-size="{size}" fill="{TEXT}">{escape(p["now"])}</text>', t + .15)
    t = command(364, "status", t + .6)
    output(
        f'<circle cx="{x0 + 5}" cy="392" r="5" fill="{POSITIVE}"/>'
        f'<text x="{x0 + 22}" y="398" font-family="{MONO}" font-size="{size}" fill="{TEXT}">{escape(p["status"])}</text>',
        t + .15,
    )
    end = t + .6
    commits = recent_commits(user) if user else []
    if commits:
        px = 696
        parts.append(f'  <path d="M656 49V{h - 1}" {HAIR}/>')
        ct = command(104, "git log --oneline", 1.4, x0=px)
        for i, (_, sha, repo, msg) in enumerate(commits):
            y = 156 + i * 56
            msg = msg if len(msg) <= 38 else msg[:37].rstrip() + "…"
            output(
                f'<text x="{px}" y="{y}" font-family="{MONO}" font-size="16" fill="{MUTED}">{escape(sha)}'
                f'<tspan dx="12" fill="{TEXT}">{escape(msg)}</tspan></text>'
                f'<text x="{px + 7 * 9.6 + 12:.0f}" y="{y + 22}" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(repo)}</text>',
                ct + .15 + i * .06,
            )
    output(
        f'<text x="{x0}" y="444" font-family="{MONO}" font-size="{size}" fill="{ACCENT}">&gt;</text>'
        f'<rect class="cursor" x="{x0 + 2 * cw:.1f}" y="428" width="10" height="21" fill="{ACCENT}"/>',
        end,
    )

    body = f"""{frame(w, h)}
  <path d="M1 48H{w - 1}" {HAIR}/>
  <circle cx="28" cy="24" r="6" fill="{TEXT}" fill-opacity=".14"/><circle cx="48" cy="24" r="6" fill="{TEXT}" fill-opacity=".14"/><circle cx="68" cy="24" r="6" fill="{TEXT}" fill-opacity=".14"/>
  <text x="{w / 2:.0f}" y="29" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(p["username"])} — zsh</text>
{chr(10).join(parts)}"""
    style = (
        RISE
        + "\n" + "\n".join(styles)
        + "\n@keyframes on { from { opacity: 1; } to { opacity: 1; } }"
        + "\n.cursor { animation: blink 1.1s steps(1) infinite; } @keyframes blink { 50% { opacity: 0; } }"
    )
    return svg(w, h, f'{p["name"]}, {p["role"]} at {p["org"]}. {p["now"]}, {p["status"]}.', body, style)


def footer(theme):
    w, h = 1200, 72
    c = {"dark": {"text": TEXT, "muted": MUTED, "accent": ACCENT}, "light": LIGHT}[theme]
    body = f"""
  <path d="M0 .5H{w}" stroke="{c["text"]}" stroke-opacity=".1"/>
  <text x="0" y="46" font-family="{MONO}" font-size="16" fill="{c["accent"]}">&gt;</text>
  <text x="24" y="46" font-family="{MONO}" font-size="16" fill="{c["muted"]}">exit</text>
  <text x="{w}" y="46" text-anchor="end" font-family="{MONO}" font-size="16" fill="{c["muted"]}">{escape(PROFILE["site"])}</text>"""
    return svg(w, h, PROFILE["site"], body)


def section(title, theme):
    w, h = 1200, 72
    c = {"dark": {"text": TEXT, "accent": ACCENT}, "light": LIGHT}[theme]
    label = f"~/{title}"
    line_x = text_width(label, 22, mono=True) + 24
    body = f"""
  <text x="0" y="44" font-family="{MONO}" font-size="22" fill="{c["text"]}"><tspan fill="{c["accent"]}">~/</tspan>{escape(title)}</text>
  <rect class="draw" x="{line_x:.0f}" y="37" width="{w - line_x:.0f}" height="1" fill="{c["text"]}" fill-opacity=".1"/>"""
    style = f".draw {{ transform-origin: {line_x:.0f}px 0; animation: draw .5s {EASE} .1s both; }} @keyframes draw {{ from {{ transform: scaleX(0); }} }}"
    return svg(w, h, title, body, style)


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

    colors = {"kw": ACCENT, "v": TEXT, "p": MUTED, "k": SECOND, "s": TEXT}
    top, lh = 96, 32
    h = top + lh * (len(rows) - 1) + 40
    lines = []
    for i, row in enumerate(rows):
        spans = "".join(f'<tspan fill="{colors[k]}">{escape(t)}</tspan>' for k, t in row)
        y = top + i * lh
        lines.append(
            f'  <g class="ln" style="animation-delay:{.15 + i * .05:.2f}s">'
            f'<text x="56" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{MUTED}" fill-opacity=".6">{i + 1}</text>'
            f'<text x="80" y="{y}" font-family="{MONO}" font-size="18" xml:space="preserve">{spans}</text></g>'
        )
    body = f"""{frame(w, h)}
  <path d="M1 48H{w - 1}" {HAIR}/>
  <text x="24" y="29" font-family="{MONO}" font-size="13" fill="{MUTED}">about.ts</text>
{chr(10).join(lines)}"""
    style = f".ln {{ opacity: 0; animation: ln .4s {EASE} forwards; }} @keyframes ln {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}"
    return svg(w, h, "About Dhruv: " + ", ".join(f"{k} {v}" for k, v in PROFILE["about"] if not isinstance(v, list)), body, style)


def arrow(x, y):
    return f'<path d="M{x} {y + 12} L{x + 12} {y} M{x + 3} {y} H{x + 12} V{y + 9}" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'


def featured_card():
    p = PROFILE["featured"]
    w, h = 1200, 260
    desc = wrap(p["desc"], 56)[:3]
    desc_svg = "".join(
        f'<text x="40" y="{132 + j * 28}" font-family="{SANS}" font-size="18" fill="{SECOND}">{escape(line)}</text>' for j, line in enumerate(desc)
    )
    figure, caption = p["figure"]
    body = f"""{frame(w, h)}
  <g class="rise">
    <text x="40" y="56" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(p["kind"])}</text>
    <text x="40" y="96" font-family="{SANS}" font-size="32" font-weight="500" letter-spacing="-.6" fill="{TEXT}">{escape(p["title"])}</text>
    {desc_svg}
    <text x="40" y="224" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape("  ·  ".join(p["tags"]))}</text>
  </g>
  <path d="M760 40V{h - 40}" {HAIR}/>
  <g class="rise" style="animation-delay:.12s">
    <text x="800" y="150" font-family="{SANS}" font-size="96" font-weight="500" letter-spacing="-3" fill="{ACCENT}" style="{NUM}">{escape(figure)}</text>
    <text x="804" y="190" font-family="{SANS}" font-size="16" fill="{SECOND}">{escape(caption)}</text>
  </g>
  {arrow(w - 52, 40)}"""
    return svg(w, h, f'{p["title"]}: {p["desc"]}', body, RISE)


def project_card(p, i):
    w, h = 392, 236
    desc = wrap(p["desc"], 38)[:3]
    desc_svg = "".join(
        f'<text x="28" y="{120 + j * 24}" font-family="{SANS}" font-size="15.5" fill="{SECOND}">{escape(line)}</text>' for j, line in enumerate(desc)
    )
    body = f"""{frame(w, h)}
  <g class="rise" style="animation-delay:{.08 + i * .06:.2f}s">
    <text x="28" y="48" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(p["kind"])}</text>
    <text x="28" y="84" font-family="{SANS}" font-size="22" font-weight="500" letter-spacing="-.3" fill="{TEXT}">{escape(p["title"])}</text>
    {desc_svg}
    <text x="28" y="{h - 28}" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape("  ·  ".join(p["tags"]))}</text>
  </g>
  {arrow(w - 44, 34)}"""
    return svg(w, h, f'{p["title"]}: {p["desc"]}', body, RISE)


ICONS = {
    "globe": f'<circle r="8" fill="none" stroke="{SECOND}" stroke-width="1.5"/><ellipse rx="3.5" ry="8" fill="none" stroke="{SECOND}" stroke-width="1.5"/><path d="M-8 0H8" stroke="{SECOND}" stroke-width="1.5"/>',
    "linkedin": f'<rect x="-8" y="-8" width="16" height="16" rx="3" fill="none" stroke="{SECOND}" stroke-width="1.5"/><path d="M-4 -1V4.5M-4 -4.2V-4M0 4.5V-1M0 1.5C0 -.5 4 -1.5 4 1.5V4.5" fill="none" stroke="{SECOND}" stroke-width="1.5" stroke-linecap="round"/>',
    "mail": f'<rect x="-8.5" y="-6.5" width="17" height="13" rx="2.5" fill="none" stroke="{SECOND}" stroke-width="1.5"/><path d="M-7.5 -5 L0 1 L7.5 -5" fill="none" stroke="{SECOND}" stroke-width="1.5" stroke-linejoin="round"/>',
}


def button(label, icon):
    w, h = 168, 48
    body = f"""{frame(w, h, r=10, fill=RAISED)}
  <path d="M10 1.5H{w - 10}" stroke="#FFFFFF" stroke-opacity=".08"/>
  <g transform="translate(28 24)">{ICONS[icon]}</g>
  <text x="48" y="29.5" font-family="{SANS}" font-size="15" font-weight="500" fill="{TEXT}">{escape(label)}</text>"""
    return svg(w, h, label, body)


QUERY = """
query($login: String!) {
  user(login: $login) {
    recent: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 6, orderBy: {field: PUSHED_AT, direction: DESC}) {
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
        f'  <text x="32" y="52" font-family="{SANS}" font-size="17" font-weight="500" fill="{TEXT}">{escape(title)}</text>'
        f'<text x="{w - 32}" y="52" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(meta)}</text>'
    )


def stats_card(user):
    w, h = 708, 300
    days = days_of(user)
    current, longest = streaks(days)
    cc = user["contributionsCollection"]
    items = [
        ("Contributions", cc["contributionCalendar"]["totalContributions"]),
        ("Commits", cc["totalCommitContributions"]),
        ("Active days", sum(1 for d in days if d["contributionCount"])),
        ("Longest streak", f"{longest}d"),
        ("Current streak", f"{current}d"),
        ("Public repos", user["repositories"]["totalCount"]),
    ]
    cells = []
    for i, (label, value) in enumerate(items):
        x, y = 32 + (i % 3) * 220, 132 + (i // 3) * 104
        shown = f"{value:,}" if isinstance(value, int) else value
        cells.append(
            f'  <g class="rise" style="animation-delay:{.05 + i * .05:.2f}s">'
            f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="32" font-weight="500" letter-spacing="-.6" fill="{ACCENT if i == 0 else TEXT}" style="{NUM}">{shown}</text>'
            f'<text x="{x}" y="{y + 28}" font-family="{SANS}" font-size="14" fill="{SECOND}">{label}</text></g>'
        )
    body = f"{frame(w, h)}\n{card_head(w, 'GitHub', 'last 12 months')}\n" + "\n".join(cells)
    return svg(w, h, "GitHub stats for the last 12 months", body, RISE)


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
        y = 104 + i * 40
        bar_w = (w - 64) * size / lead
        rows.append(
            f'  <text x="32" y="{y}" font-family="{SANS}" font-size="15" fill="{TEXT}">{escape(name)}</text>'
            f'<text x="{w - 32}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUTED}" style="{NUM}">{size / total:.0%}</text>'
            f'<rect x="32" y="{y + 10}" width="{w - 64}" height="4" rx="2" fill="{TEXT}" fill-opacity=".06"/>'
            f'<rect class="bar" style="animation-delay:{.1 + i * .05:.2f}s" x="32" y="{y + 10}" width="{bar_w:.1f}" height="4" rx="2" fill="{ACCENT if i == 0 else SECOND}" fill-opacity="{1 if i == 0 else .45}"/>'
        )
    body = f"{frame(w, h)}\n{card_head(w, 'Languages', 'by code size')}\n" + "\n".join(rows)
    style = f".bar {{ transform-origin: 32px 0; transform: scaleX(0); animation: bar .7s {EASE} forwards; }} @keyframes bar {{ to {{ transform: scaleX(1); }} }}"
    return svg(w, h, "Most used languages: " + ", ".join(n for n, _ in top), body, style)


def contributions_card(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"][-53:]
    step, cell = 20.4, 16
    w = 1200
    gx, gy = (w - (len(weeks) - 1) * step - cell) / 2, 104
    h = int(gy + 7 * step + 56)
    peak = max((d["contributionCount"] for wk in weeks for d in wk["contributionDays"]), default=0) or 1
    scale = ["#1C1C26", "#2F2752", "#4A3A8E", "#7458D6", "#A68CFF"]

    def level(n):
        return 0 if n == 0 else min(4, 1 + int(3.999 * n / peak))

    cells, months, last_month = [], [], None
    for wi, wk in enumerate(weeks):
        x = gx + wi * step
        for d in wk["contributionDays"]:
            day = date.fromisoformat(d["date"])
            y = gy + ((day.weekday() + 1) % 7) * step
            cells.append(
                f'<rect class="c" style="animation-delay:{.1 + wi * .014:.3f}s" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="4" fill="{scale[level(d["contributionCount"])]}"/>'
            )
        first = date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                months.append(f'<text x="{x:.1f}" y="{gy - 14}" font-family="{MONO}" font-size="12" fill="{MUTED}">{first.strftime("%b")}</text>')
            last_month = first.month

    ly = h - 28
    legend = "".join(f'<rect x="{w - 168 + i * 20}" y="{ly - 12}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(scale))
    body = (
        f"{frame(w, h)}\n{card_head(w, 'Contributions', '')}"
        f'<text x="{w - 32}" y="52" text-anchor="end" font-family="{SANS}" font-size="17" fill="{SECOND}"><tspan fill="{TEXT}" font-weight="500" style="{NUM}">{cal["totalContributions"]:,}</tspan> in the last year</text>'
        + "\n  " + "".join(months)
        + "\n  " + "\n  ".join(cells)
        + f'\n  <text x="{w - 180}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">less</text>{legend}'
        + f'<text x="{w - 64}" y="{ly}" font-family="{MONO}" font-size="12" fill="{MUTED}">more</text>'
    )
    style = f".c {{ opacity: 0; animation: c .4s {EASE} forwards; }} @keyframes c {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}"
    return svg(w, h, f'{cal["totalContributions"]} contributions in the last year', body, style)


def main():
    OUT.mkdir(exist_ok=True)
    files = {"about.svg": code_card(), "project-" + PROFILE["featured"]["slug"] + ".svg": featured_card()}
    for theme in ("dark", "light"):
        files[f"footer-{theme}.svg"] = footer(theme)
        for slug, title in PROFILE["sections"]:
            files[f"section-{slug}-{theme}.svg"] = section(title, theme)
    for i, project in enumerate(PROFILE["projects"]):
        files[f'project-{project["slug"]}.svg'] = project_card(project, i)
    for slug, label, icon in PROFILE["buttons"]:
        files[f"button-{slug}.svg"] = button(label, icon)

    try:
        user = fetch_github()
    except Exception as err:  # keep the last good cards if the API call fails
        print(f"GitHub API failed, keeping existing stats cards: {err}")
        user = None
    files["header.svg"] = header(user)
    if user:
        files["stats.svg"] = stats_card(user)
        files["languages.svg"] = languages_card(user)
        files["contributions.svg"] = contributions_card(user)
    elif not github_token():
        print("No GitHub token found, keeping existing stats cards.")

    for old in ("header-dark.svg", "header-light.svg", "footer.svg"):
        (OUT / old).unlink(missing_ok=True)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(f"Wrote {len(files)} files to {OUT}")


if __name__ == "__main__":
    main()
