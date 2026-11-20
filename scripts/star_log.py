"""Generate assets/star-log.svg: a galaxy pixel-art contribution log.

Reads the user's contribution calendar from the GitHub GraphQL API.
Token comes from GITHUB_TOKEN or GH_TOKEN; username from PROFILE_USER (default b00001).
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request

USER = os.environ.get("PROFILE_USER", "b00001")
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "star-log.svg"

BG, PANEL, SLOT = "#07070a", "#111114", "#1a1a1f"
YEL, YEL_D = "#ffd23f", "#c99a00"
RED, RED_D = "#e63946", "#9d1c26"
WHITE, DIM, FAINT = "#f5f5f5", "#8a8a8f", "#2a2a30"
HEAD = "font-family=\"'Press Start 2P','Courier New',monospace\""
BODY = "font-family=\"'Courier New',monospace\""

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel weekday}}}}}}"""

CELL, STEP = 10, 13
GX, GY = 74, 104  # grid origin
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "star-log"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def fmt(d):
    return f"{d:%b} {d.day}".lower()


def stats(days):
    """days: list of (date, count) sorted ascending, ending today."""
    total = sum(c for _, c in days)
    active = sum(1 for _, c in days if c)
    best = max(days, key=lambda x: (x[1], x[0]))
    # longest streak
    longest, run, start, lrange = 0, 0, None, None
    for d, c in days:
        if c:
            run += 1
            start = d if run == 1 else start
            if run >= longest:
                longest, lrange = run, (start, d)
        else:
            run = 0
    # current streak: today may still be empty without breaking it
    cur = 0
    seq = days[:-1] if days and days[-1][1] == 0 else days
    for _, c in reversed(seq):
        if not c:
            break
        cur += 1
    return total, active, best, cur, longest, lrange


def star(x, y, lvl, cls=""):
    """Pixel glyph for one day inside a CELL x CELL box."""
    c = f' class="{cls}"' if cls else ""
    if lvl == 0:
        return f'<rect x="{x+4}" y="{y+4}" width="2" height="2" fill="{FAINT}"/>'
    if lvl == 1:
        return f'<rect x="{x+3}" y="{y+3}" width="4" height="4" fill="{RED_D}"/>'
    col = {2: RED, 3: YEL, 4: YEL}[lvl]
    core = WHITE if lvl == 4 else (YEL_D if lvl == 3 else RED_D)
    return (f'<g{c}><rect x="{x+4}" y="{y}" width="2" height="10" fill="{col}"/>'
            f'<rect x="{x}" y="{y+4}" width="10" height="2" fill="{col}"/>'
            f'<rect x="{x+3}" y="{y+3}" width="4" height="4" fill="{col}"/>'
            f'<rect x="{x+4}" y="{y+4}" width="2" height="2" fill="{core}"/></g>')


def rocket():
    px = [  # (x, y, w, h, colour) — a small rocket pointing right
        (0, 4, 2, 2, RED), (2, 2, 4, 6, WHITE), (6, 3, 4, 4, WHITE), (10, 4, 2, 2, RED),
        (5, 4, 2, 2, YEL), (2, 0, 2, 2, RED), (2, 8, 2, 2, RED),
    ]
    body = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>' for x, y, w, h, c in px)
    flame = (f'<g class="flame"><rect x="-4" y="4" width="4" height="2" fill="{YEL}"/>'
             f'<rect x="-7" y="4" width="3" height="2" fill="{RED}"/></g>')
    return f'<g class="rocket"><g transform="translate(0 0)">{flame}{body}</g></g>'


def card(x, y, w, label, value, unit, lc=YEL):
    h = 50
    return (f'<rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" fill="{RED_D}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{DIM}"/>'
            f'<rect x="{x+2}" y="{y+2}" width="{w-4}" height="{h-4}" fill="{BG}"/>'
            f'<text x="{x+10}" y="{y+17}" {HEAD} font-size="9" fill="{lc}">{label}</text>'
            f'<text x="{x+10}" y="{y+40}" {BODY} font-size="20" font-weight="bold" fill="{WHITE}">{value}</text>'
            f'<text x="{x+12+len(str(value))*12}" y="{y+40}" {BODY} font-size="10" fill="{DIM}">{unit}</text>')


def build(cal):
    weeks = cal["weeks"]
    today = dt.date.fromisoformat(weeks[-1]["contributionDays"][-1]["date"])
    flat = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in weeks for d in w["contributionDays"]]
    total, active, best, cur, longest, lrange = stats(flat)
    lset = set()
    if lrange:
        d = lrange[0]
        while d <= lrange[1]:
            lset.add(d)
            d += dt.timedelta(days=1)

    W, H = 840, 318
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">',
         "<style>"
         "@keyframes tw{0%,100%{opacity:1}50%{opacity:.35}}"
         "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
         "@keyframes fly{0%{transform:translate(60px,0)}100%{transform:translate(780px,0)}}"
         "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}"
         "@keyframes flick{0%,100%{opacity:1}50%{opacity:.3}}"
         ".tw{animation:tw 2.4s steps(2,end) infinite}"
         ".tw2{animation:tw 3.1s steps(2,end) .8s infinite}"
         ".today{animation:blink 1.2s steps(1,end) infinite}"
         ".rocket{animation:fly 16s linear infinite}"
         ".rocket>g{animation:bob 1.6s steps(2,end) infinite}"
         ".flame{animation:flick .3s steps(2,end) infinite}"
         "</style>",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    # background stars
    for i, (sx, sy) in enumerate([(40, 70), (300, 24), (520, 18), (700, 30), (790, 24), (160, 20), (460, 26), (812, 120)]):
        o.append(f'<rect class="{"tw" if i % 2 else "tw2"}" x="{sx}" y="{sy}" width="2" height="2" fill="{WHITE if i % 3 else YEL}"/>')

    # panel frame: red offset shadow, yellow border, white highlight, dark interior
    px, py, pw, ph = 12, 34, 808, 272
    o += [f'<rect x="{px+6}" y="{py+6}" width="{pw}" height="{ph}" fill="{RED_D}"/>',
          f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{YEL}"/>',
          f'<rect x="{px}" y="{py}" width="{pw}" height="3" fill="{WHITE}"/>',
          f'<rect x="{px}" y="{py}" width="3" height="{ph}" fill="{WHITE}"/>',
          f'<rect x="{px+5}" y="{py+5}" width="{pw-10}" height="{ph-10}" fill="{PANEL}"/>']
    # tab
    o += [f'<rect x="{px+6}" y="16" width="176" height="24" fill="{RED_D}"/>',
          f'<rect x="{px}" y="10" width="176" height="29" fill="{YEL}"/>',
          f'<rect x="{px}" y="10" width="176" height="3" fill="{WHITE}"/>',
          f'<rect x="{px}" y="10" width="3" height="29" fill="{WHITE}"/>',
          f'<rect x="{px+5}" y="15" width="166" height="25" fill="{PANEL}"/>',
          f'<g transform="translate({px+14} 22)"><rect x="4" y="0" width="2" height="10" fill="{YEL}"/>'
          f'<rect x="0" y="4" width="10" height="2" fill="{YEL}"/><rect x="3" y="3" width="4" height="4" fill="{YEL}"/></g>',
          f'<text x="{px+32}" y="32" {HEAD} font-size="11" fill="{YEL}">STAR LOG</text>',
          f'<text x="806" y="62" text-anchor="end" {BODY} font-size="11" fill="{DIM}">@{USER} · contributions, last 12 months</text>']
    # corner jewels
    for jx, jy in [(px + pw - 9, py + 9), (px + 9, py + ph - 13)]:
        o.append(f'<rect x="{jx}" y="{jy}" width="4" height="4" fill="{RED}"/>')

    # rocket flight lane + dotted horizon
    for x in range(GX - 6, GX + 53 * STEP, 8):
        o.append(f'<rect x="{x}" y="{GY-20}" width="3" height="1" fill="{FAINT}"/>')
    o.append(f'<g transform="translate(0 {GY-34})">{rocket()}</g>')

    # month + weekday labels
    last_m = None
    for wi, w in enumerate(weeks):
        d0 = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if d0.month != last_m and d0.day <= 7 and wi < 52:
            month = f"{d0:%b}".lower()
            o.append(f'<text x="{GX + wi*STEP}" y="{GY-6}" {BODY} font-size="10" fill="{DIM}">{month}</text>')
            last_m = d0.month
        elif last_m is None:
            last_m = d0.month
    for wd, name in [(1, "mon"), (3, "wed"), (5, "fri")]:
        o.append(f'<text x="{GX-8}" y="{GY + wd*STEP + 9}" text-anchor="end" {BODY} font-size="10" fill="{DIM}">{name}</text>')

    # constellation line through the longest streak
    pts = []
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            if dt.date.fromisoformat(d["date"]) in lset:
                pts.append((GX + wi*STEP + 5, GY + d["weekday"]*STEP + 5))
    if len(pts) > 1:
        path = " ".join(f"{x},{y}" for x, y in pts)
        o.append(f'<polyline points="{path}" fill="none" stroke="{YEL_D}" stroke-width="1" stroke-dasharray="2 2" opacity="0.7" shape-rendering="auto"/>')

    # the stars
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            x, y = GX + wi*STEP, GY + d["weekday"]*STEP
            lv = LEVELS.get(d["contributionLevel"], 0)
            cls = "tw" if lv == 4 else ("tw2" if lv == 3 and (wi + d["weekday"]) % 3 == 0 else "")
            o.append(star(x, y, lv, cls))
            if dt.date.fromisoformat(d["date"]) == today:
                o.append(f'<rect class="today" x="{x-2}" y="{y-2}" width="{CELL+4}" height="{CELL+4}" fill="none" stroke="{WHITE}" stroke-width="2"/>')

    # legend
    ly = GY + 7*STEP + 12
    o.append(f'<rect x="{GX}" y="{ly}" width="10" height="10" fill="none" stroke="{WHITE}" stroke-width="2"/>'
             f'<text x="{GX+16}" y="{ly+9}" {BODY} font-size="10" fill="{DIM}">today</text>'
             f'<line x1="{GX+64}" y1="{ly+5}" x2="{GX+84}" y2="{ly+5}" stroke="{YEL_D}" stroke-dasharray="2 2"/>'
             f'<text x="{GX+90}" y="{ly+9}" {BODY} font-size="10" fill="{DIM}">longest streak</text>')
    lx = 806 - 42 - 5*14
    o.append(f'<text x="{lx-6}" y="{ly+9}" text-anchor="end" {BODY} font-size="10" fill="{DIM}">dim</text>')
    for i in range(5):
        o.append(star(lx + i*14, ly, i))
    o.append(f'<text x="806" y="{ly+9}" text-anchor="end" {BODY} font-size="10" fill="{DIM}">bright</text>')

    # stat cards
    cy, cw, gap = ly + 26, 146, 9
    lr = f"{fmt(lrange[0])}-{fmt(lrange[1]).split()[-1] if lrange[0].month == lrange[1].month else fmt(lrange[1])}" if lrange else "-"
    cards = [("TOTAL", total, "contributions", YEL),
             ("STREAK", cur, "day now" if cur == 1 else "days now", RED),
             ("LONGEST", longest, lr, YEL),
             ("BEST DAY", best[1], fmt(best[0]) if best[1] else "-", RED),
             ("ACTIVE", active, "days lit", YEL)]
    for i, (lab, val, unit, lc) in enumerate(cards):
        o.append(card(30 + i*(cw+gap), cy, cw, lab, val, unit, lc))

    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    OUT.write_text(build(fetch()), encoding="utf-8")
    print(f"wrote {OUT}")
