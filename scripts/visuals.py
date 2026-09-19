"""Animated, self-contained SVGs generated from the saved profile snapshot."""

from collections import Counter
from datetime import date, datetime
from html import escape
import math


INK = "#070914"
PANEL = "#101527"
WHITE = "#f4f7ff"
MUTED = "#a9b2c7"
LINE = "#28324d"
CYAN = "#45d9ff"
BLUE = "#4b72ff"
PURPLE = "#a56eff"
PINK = "#ff5ca8"
ORANGE = "#ff7a45"
YELLOW = "#ffd84d"
GREEN = "#49e39b"
RAINBOW = [GREEN, "#8ddd55", YELLOW, ORANGE, PINK, PURPLE, BLUE, CYAN]
LANGUAGE_COLORS = {
    "Python": CYAN, "JavaScript": YELLOW, "TypeScript": BLUE,
    "Java": ORANGE, "HTML": "#ff6542", "CSS": PURPLE,
    "C": "#aab7cf", "C++": PINK, "Jupyter Notebook": "#f39a45",
    "Dart": "#37d3c8", "Shell": GREEN, "Kotlin": "#d26dff",
    "Unspecified": "#64718c", "Other": "#8b95aa",
}


def _e(value):
    return escape(str(value), quote=True)


def _number(value):
    try:
        return max(0, int(value))
    except (ValueError, TypeError, OverflowError):
        return 0


def _text(x, y, value, size=22, fill=WHITE, weight=400, extra=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-weight="{weight}" {extra}>{_e(value)}</text>')


def _start(height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" '
        f'viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{_e(title)}</title>',
        f'<desc id="desc">{_e(description)}</desc>',
        '<defs>',
        '<linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#11172a"/><stop offset=".55" stop-color="#070914"/>'
        '<stop offset="1" stop-color="#141027"/></linearGradient>',
        '<linearGradient id="rainbow" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="{GREEN}"/><stop offset=".2" stop-color="{YELLOW}"/>'
        f'<stop offset=".42" stop-color="{ORANGE}"/><stop offset=".62" stop-color="{PINK}"/>'
        f'<stop offset=".82" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/>'
        '</linearGradient>',
        '<filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="6"/></filter>',
        '</defs>',
        '<style>'
        '@keyframes enter{0%{opacity:0;transform:translateY(12px)}18%,100%{opacity:1;transform:translateY(0)}}'
        '@keyframes scan{0%,10%{transform:translateX(0)}90%,100%{transform:translateX(190px)}}'
        '@keyframes orbit{to{stroke-dashoffset:-120}}'
        '@keyframes pulse{0%,100%{opacity:.32}50%{opacity:1}}'
        '@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}'
        '@keyframes hue{to{filter:hue-rotate(360deg)}}'
        '@keyframes sparkle{0%,100%{opacity:.2;transform:scale(.65)}50%{opacity:1;transform:scale(1.2)}}'
        '@keyframes cityCycle{0%,38%,100%{opacity:1}48%,82%{opacity:.08}}'
        '@keyframes logoCycle{0%,38%,100%{opacity:.05}48%,82%{opacity:1}}'
        '@keyframes build{0%,100%{transform:translateY(0)}45%{transform:translateY(-12px)}}'
        '@keyframes blockHop{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}'
        '.enter{opacity:1;animation:enter 5s ease-out infinite}'
        '.scan{animation:scan 6s cubic-bezier(.65,0,.35,1) infinite alternate}'
        '.orbit{animation:orbit 8s linear infinite}'
        '.pulse{animation:pulse 3s ease-in-out infinite}'
        '.float{animation:float 5s ease-in-out infinite}'
        '.city{animation:hue 18s linear infinite}'
        '.spark{transform-box:fill-box;transform-origin:center;animation:sparkle 2.8s ease-in-out infinite}'
        '.city-mode{animation:cityCycle 16s ease-in-out infinite}'
        '.logo-mode{opacity:.05;animation:logoCycle 16s ease-in-out infinite}'
        '.tower{animation:build 8s ease-in-out infinite}'
        '.logo-cube{animation:blockHop 4s ease-in-out infinite}'
        '@media(prefers-reduced-motion:reduce){'
        '.enter,.scan,.orbit,.pulse,.float,.city,.spark,.city-mode,.tower,.logo-cube{animation:none!important;opacity:1!important}'
        '.logo-mode{animation:none!important;opacity:.05!important}}'
        '</style>',
        f'<rect x=".75" y=".75" width="1198.5" height="{height-1.5}" rx="18" '
        f'fill="url(#surface)" stroke="{LINE}" stroke-width="1.5"/>',
    ]


def _end(parts):
    return "\n".join(parts + ["</svg>"]) + "\n"


def _calendar(snapshot):
    unique = {}
    for entry in (snapshot.get("contributions") or {}).get("days", []):
        try:
            day = date.fromisoformat(entry["date"])
        except (KeyError, TypeError, ValueError):
            continue
        unique[day] = {"date": day, "count": _number(entry.get("count")),
                       "level": min(4, _number(entry.get("level")))}
    return [unique[key] for key in sorted(unique)]


def _updated(snapshot):
    try:
        parsed = datetime.fromisoformat(snapshot.get("updated_at", "").replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y")
    except (ValueError, TypeError, AttributeError):
        return "Date unavailable"


def _streaks(days):
    longest = current = running = 0
    for day in days:
        if day["count"]:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    for day in reversed(days):
        if not day["count"]:
            break
        current += 1
    return current, longest


def render_dashboard(snapshot):
    repos = [repo for repo in snapshot.get("repos", []) if not repo.get("fork", False)]
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max((day["count"] for day in days), default=0)
    current, longest = _streaks(days)
    streak_arc = max(18, 383.27 * current / max(1, longest)) if current else 0
    stars = sum(_number(repo.get("stargazers_count")) for repo in repos)
    followers = _number((snapshot.get("user") or {}).get("followers"))
    parts = _start(
        600, "GitHub statistics",
        f"{len(repos)} public non-fork repositories, {stars} stars received across those repositories, "
        f"and {followers} followers. "
        + (f"{total} contributions in the returned calendar. " if days else "Contribution calendar unavailable. ")
        + "Language mix counts each repository's primary language once; it does not measure code volume or proficiency.",
    )
    parts += [
        _text(44, 58, "GitHub statistics", 31, WHITE, 700),
        _text(1156, 58, f"LIVE FROM THE SAVED SNAPSHOT · {_updated(snapshot).upper()}", 15, MUTED, 500,
              'text-anchor="end" letter-spacing="1"'),
        f'<path d="M44 83H1156" stroke="{LINE}"/>',
    ]
    stat_colors = [CYAN, PINK, PURPLE, YELLOW]
    stats = [(len(repos), "PUBLIC REPOSITORIES"), (stars, "STARS RECEIVED"),
             (followers, "FOLLOWERS"), (total if days else None, "CONTRIBUTIONS")]
    for index, (value, label) in enumerate(stats):
        x = 44 + index * 278
        color = stat_colors[index]
        parts += [
            f'<g class="enter" style="animation-delay:-{index * .35}s">',
            f'<rect x="{x}" y="108" width="254" height="118" rx="13" fill="{PANEL}" stroke="{LINE}"/>',
            f'<rect x="{x}" y="108" width="254" height="5" rx="2.5" fill="{color}"/>',
            f'<rect class="scan" x="{x+10}" y="111" width="44" height="2" fill="{WHITE}" opacity=".9"/>',
            _text(x + 20, 173, f"{value:,}" if value is not None else "—", 53, WHITE, 750,
                  'letter-spacing="-2"'),
            _text(x + 20, 207, label, 15, color, 650, 'letter-spacing=".8"'),
            '</g>',
        ]

    languages = Counter(repo.get("language") or "Unspecified" for repo in repos)
    ranked = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(amount for _, amount in ranked[5:]))]
    parts += [
        '<rect x="44" y="252" width="688" height="306" rx="15" fill="#0d1221" stroke="#293451"/>',
        _text(70, 293, "Language constellation", 23, WHITE, 650),
        _text(706, 293, "PRIMARY LANGUAGE · REPOSITORY COUNT", 13, MUTED, 500,
              'text-anchor="end" letter-spacing=".8"'),
    ]
    if ranked and repos:
        circumference = 326.73
        offset = 0.0
        parts.append(f'<circle cx="197" cy="414" r="52" fill="none" stroke="{LINE}" stroke-width="22"/>')
        for index, (language, count) in enumerate(ranked):
            color = LANGUAGE_COLORS.get(language, PURPLE)
            segment = circumference * count / len(repos)
            visible = max(0.1, segment - 4)
            parts += [
                f'<circle cx="197" cy="414" r="52" fill="none" stroke="{color}" stroke-width="22" '
                f'stroke-linecap="round" stroke-dasharray="{visible:.2f} {circumference-visible:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 197 414)">',
                f'<animate attributeName="stroke-dasharray" values="0 {circumference:.2f};'
                f'{visible:.2f} {circumference-visible:.2f};{visible:.2f} {circumference-visible:.2f}" '
                'keyTimes="0;.22;1" dur="7s" repeatCount="indefinite"/>',
                '</circle>',
            ]
            offset += segment
        parts += [_text(197, 409, len(repos), 33, WHITE, 750, 'text-anchor="middle"'),
                  _text(197, 438, "REPOS", 13, MUTED, 650, 'text-anchor="middle" letter-spacing="1"')]
        for index, (language, count) in enumerate(ranked):
            x = 310 + (index % 2) * 205
            y = 350 + (index // 2) * 61
            color = LANGUAGE_COLORS.get(language, PURPLE)
            percentage = count * 100 / len(repos)
            parts += [f'<circle class="pulse" cx="{x}" cy="{y-7}" r="6" fill="{color}" '
                      f'style="animation-delay:-{index*.4}s"/>',
                      _text(x + 17, y, language, 18, WHITE, 550),
                      _text(x + 17, y + 23, f"{count} repos · {percentage:.0f}%", 14, MUTED)]
    else:
        parts.append(_text(70, 380, "No public repository language data available.", 21, MUTED))

    parts += [
        '<rect x="756" y="252" width="400" height="306" rx="15" fill="#0d1221" stroke="#293451"/>',
        _text(782, 293, "Contribution rhythm", 23, WHITE, 650),
        f'<circle cx="882" cy="405" r="61" fill="none" stroke="{LINE}" stroke-width="12"/>',
        f'<circle class="orbit" cx="882" cy="405" r="61" fill="none" stroke="{CYAN}" stroke-width="12" '
        f'stroke-linecap="round" stroke-dasharray="{streak_arc:.2f} {383.27-streak_arc:.2f}" '
        'transform="rotate(-90 882 405)"/>',
        f'<circle class="pulse" cx="882" cy="344" r="9" fill="{ORANGE}"/>',
        _text(882, 421, current, 43, WHITE, 750, 'text-anchor="middle"'),
        _text(882, 491, "CURRENT STREAK", 14, ORANGE, 700, 'text-anchor="middle" letter-spacing=".9"'),
        _text(1042, 359, longest, 34, PURPLE, 700, 'text-anchor="middle"'),
        _text(1042, 385, "LONGEST", 13, MUTED, 650, 'text-anchor="middle" letter-spacing=".8"'),
        _text(1042, 446, active, 34, GREEN, 700, 'text-anchor="middle"'),
        _text(1042, 472, "ACTIVE DAYS", 13, MUTED, 650, 'text-anchor="middle" letter-spacing=".8"'),
        _text(1042, 522, f"BEST DAY · {best}", 14, YELLOW, 650, 'text-anchor="middle"'),
    ]
    return _end(parts)


def _trophy(cx, cy, color):
    return [
        f'<g class="float" style="transform-origin:{cx}px {cy}px">',
        f'<path d="M{cx-34} {cy-38}h68v28c0 31-14 48-34 48s-34-17-34-48z" fill="{color}"/>',
        f'<path d="M{cx-34} {cy-27}h-23v11c0 24 14 37 37 37M{cx+34} {cy-27}h23v11c0 24-14 37-37 37" '
        f'fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>',
        f'<path d="M{cx} {cy+38}v25M{cx-25} {cy+68}h50" stroke="{color}" stroke-width="11" stroke-linecap="round"/>',
        f'<circle cx="{cx}" cy="{cy-7}" r="12" fill="{INK}" opacity=".72"/>',
        '</g>',
    ]


def render_achievements(config):
    achievements = list(config.get("achievements") or [])[:4]
    parts = _start(440, "Achievement cabinet",
                   "Four verified competition milestones: " + "; ".join(
                       f"{item.get('event', '')}, {item.get('result', '')}" for item in achievements))
    parts += [_text(44, 58, "Achievement cabinet", 31, WHITE, 700),
              _text(1156, 58, "BUILT FROM REAL MILESTONES", 15, MUTED, 500,
                    'text-anchor="end" letter-spacing="1"'),
              f'<path d="M44 83H1156" stroke="{LINE}"/>']
    colors = [YELLOW, CYAN, PINK, PURPLE]
    for index, item in enumerate(achievements):
        x = 44 + index * 278
        color = colors[index]
        parts += [f'<g class="enter" style="animation-delay:-{index*.45}s">',
                  f'<rect x="{x}" y="108" width="254" height="278" rx="15" fill="{PANEL}" stroke="{LINE}"/>',
                  f'<rect x="{x}" y="108" width="254" height="6" rx="3" fill="{color}"/>']
        parts += _trophy(x + 127, 217, color)
        parts += [_text(x + 127, 311, item.get("result", ""), 25, color, 750, 'text-anchor="middle"'),
                  _text(x + 127, 344, item.get("label", ""), 17, WHITE, 600, 'text-anchor="middle"'),
                  _text(x + 127, 369, f"0{index+1} / MILESTONE", 12, MUTED, 550,
                        'text-anchor="middle" letter-spacing="1"'),
                  f'<circle class="spark" cx="{x+52}" cy="159" r="5" fill="{color}" '
                  f'style="animation-delay:-{index*.5}s"/>',
                  f'<path class="spark" d="M{x+203} 151v18m-9-9h18" stroke="{color}" stroke-width="3" '
                  f'style="animation-delay:-{index*.5+1}s"/>',
                  '</g>']
    parts += [_text(44, 418, "Competition results shown above are also listed in full in the profile.", 15, MUTED),
              '<rect class="scan" x="868" y="410" width="86" height="4" rx="2" fill="url(#rainbow)"/>']
    return _end(parts)


def _polygon(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in points)}" fill="{fill}" {extra}/>'


def _logo_cube(x, y, size, height, color, delay):
    top = [(x, y-height), (x+size, y-height+size*.55),
           (x, y-height+size*1.1), (x-size, y-height+size*.55)]
    left = [(x-size, y-height+size*.55), (x, y-height+size*1.1),
            (x, y+size*1.1), (x-size, y+size*.55)]
    right = [(x, y-height+size*1.1), (x+size, y-height+size*.55),
             (x+size, y+size*.55), (x, y+size*1.1)]
    return [f'<g class="logo-cube" style="animation-delay:-{delay:.1f}s">',
            _polygon(left, color, 'fill-opacity=".45"'),
            _polygon(right, color, 'fill-opacity=".72"'),
            _polygon(top, color, f'stroke="{INK}" stroke-width=".7"'), '</g>']


def render_contributions(snapshot):
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max((day["count"] for day in days), default=0)
    parts = _start(620 if days else 210, "GitHub contributions in 3D",
                   (f"{total} contributions over {len(days)} calendar days; {active} active days; "
                    f"best day {best} contributions. Each column is a day. Height uses a capped logarithmic scale. "
                    "Rainbow position follows the week; exact date and count appear in every column's title."
                    if days else "Contribution calendar data is unavailable."))
    parts += [_text(44, 58, "Contribution spectrum", 31, WHITE, 700),
              _text(1156, 58, f"{_updated(snapshot).upper()} · ONE COLUMN PER DAY", 15, MUTED, 500,
                    'text-anchor="end" letter-spacing="1"'),
              f'<path d="M44 83H1156" stroke="{LINE}"/>']
    if not days:
        parts.append(_text(44, 150, "Contribution calendar data is currently unavailable.", 22, MUTED))
        return _end(parts)
    first, last = days[0]["date"], days[-1]["date"]
    for x, value, label, color in [(44, total, "CONTRIBUTIONS", CYAN),
                                   (426, active, "ACTIVE DAYS", PINK),
                                   (808, best, "MOST IN ONE DAY", YELLOW)]:
        parts += [_text(x, 143, f"{value:,}", 43, color, 700),
                  _text(x, 174, label, 14, MUTED, 650, 'letter-spacing=".8"')]

    sunday_offset = (first.weekday() + 1) % 7
    slots = (last-first).days + sunday_offset + 1
    weeks = max(1, (slots+6)//7)
    step_x = min(17.1, 906/max(1, weeks-1))
    step_y = min(2.15, 114/max(1, weeks-1))
    dx, dy = min(7.5, step_x*.44), 4.25
    origin_x, origin_y = 179, 329
    end_x = origin_x + (weeks-1)*step_x
    end_y = origin_y + (weeks-1)*step_y
    platform = [(origin_x-10, origin_y-7), (end_x+15, end_y-7),
                (end_x-72, end_y+65), (origin_x-97, origin_y+65)]
    parts += [_polygon([(x, y+12) for x, y in platform], "#02030a"),
              _polygon(platform, "#11162a", f'stroke="{LINE}" stroke-width="1"')]
    for weekday in range(7):
        x = origin_x-weekday*12.5
        y = origin_y+weekday*8.6
        parts.append(f'<path d="M{x:.1f} {y:.1f}l{(weeks-1)*step_x:.1f} {(weeks-1)*step_y:.1f}" '
                     f'stroke="{LINE}" stroke-width=".6"/>')
    columns = []
    for day in days:
        offset = (day["date"]-first).days+sunday_offset
        week, weekday = divmod(offset, 7)
        x = origin_x+week*step_x-weekday*12.5
        y = origin_y+week*step_y+weekday*8.6
        height = 2 if not day["count"] else min(105, 9+math.log2(day["count"]+1)*12)
        columns.append((y, x, height, week, day))
    parts.append('<g class="city city-mode">')
    for y, x, height, week, day in sorted(columns, key=lambda cell: (cell[0], cell[1])):
        count, level = day["count"], day["level"]
        color = "#202943" if not count else RAINBOW[min(7, int(week * 8 / max(1, weeks)))]
        west = [(x-dx,y), (x,y+dy), (x,y+dy-height), (x-dx,y-height)]
        east = [(x,y+dy), (x+dx,y), (x+dx,y-height), (x,y+dy-height)]
        roof = [(x,y-dy-height),(x+dx,y-height),(x,y+dy-height),(x-dx,y-height)]
        speed = 6 + day["date"].toordinal() % 6
        delay = (day["date"].toordinal() * 7) % 10
        parts += [f'<g class="tower" style="animation-duration:{speed}s;animation-delay:-{delay}s">',
                  f'<title>{day["date"].isoformat()}: {count:,} contribution{"s" if count != 1 else ""}</title>',
                  _polygon(west, color, 'fill-opacity=".38"'),
                  _polygon(east, color, 'fill-opacity=".68"'),
                  _polygon(roof, color, f'stroke="{INK}" stroke-width=".5"')]
        if count:
            parts.append(f'<path d="M{x:.2f} {y+dy:.2f}V{y+dy-height:.2f}" '
                         f'stroke="{WHITE}" stroke-opacity=".18" stroke-width=".6"/>')
        if level == 4:
            parts.append(_polygon(roof, WHITE, f'class="pulse" opacity=".12" '
                                  f'style="animation-delay:-{(day["date"].toordinal()%12)/2}s"'))
        parts.append('</g>')
    parts.append('</g>')
    # During the alternate phase, contribution blocks gather into a GK monogram.
    logo_rows = [
        "11110 10001", "10000 10010", "10000 10100", "10111 11000",
        "10001 10100", "10001 10010", "11111 10001",
    ]
    parts.append('<g class="logo-mode">')
    for row, pattern in enumerate(logo_rows):
        for column, marker in enumerate(pattern):
            if marker != "1":
                continue
            x = 430 + column * 29
            y = 252 + row * 28
            color = RAINBOW[(row + column) % len(RAINBOW)]
            height = 23 + ((row * 11 + column * 7) % 7)
            parts += _logo_cube(x, y, 11, height, color, (row * 1.7 + column * .8) % 5)
    parts += [_text(600, 493, "CONTRIBUTIONS → GK BLOCK MODE", 15, CYAN, 650,
                    'text-anchor="middle" letter-spacing="1.2"'), '</g>']
    parts += [_text(179, 531, first.strftime("%d %b %Y"), 19, MUTED),
              _text(1110, 531, last.strftime("%d %b %Y"), 19, MUTED, 400, 'text-anchor="end"'),
              '<path d="M344 524H934m-7-4 7 4-7 4" fill="none" stroke="#485572"/>',
              f'<path d="M44 558H1156" stroke="{LINE}"/>',
              _text(44, 594, "Calendar position controls color · height uses a capped logarithmic scale", 18, MUTED),
              '<rect x="902" y="579" width="224" height="10" rx="5" fill="url(#rainbow)"/>',
              '<rect class="scan" x="902" y="576" width="42" height="16" rx="8" fill="#ffffff" opacity=".65"/>']
    return _end(parts)
