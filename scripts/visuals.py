"""Original, dependency-free SVG artwork for the GitHub profile.

The generated images are self-contained, have a useful static first frame,
and respect the viewer's reduced-motion preference. Metrics are calculated
only from the supplied snapshot; an absent calendar is never a zero calendar.
"""

from collections import Counter
from datetime import date, datetime
from html import escape
import math


INK = "#080d17"
WHITE = "#ecf4fb"
MUTED = "#99aabd"
CYAN = "#6ce5e8"
LILAC = "#baa2fa"
LIME = "#d0ed88"
LINE = "#243347"
PALETTE = [CYAN, LILAC, LIME, "#78a9fa", "#efb58c", "#66798f"]


def _e(value):
    return escape(str(value), quote=True)


def _number(value):
    try:
        return max(0, int(value))
    except (ValueError, TypeError, OverflowError):
        return 0


def _text(x, y, value, size=14, fill=WHITE, weight=400,
          family="sans", extra=""):
    fonts = ("'SFMono-Regular',Consolas,'Liberation Mono',monospace"
             if family == "mono" else "Arial,Helvetica,sans-serif")
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-family="{fonts}" font-weight="{weight}" {extra}>'
            f'{_e(value)}</text>')


def _label(x, y, value, fill=MUTED, size=11, extra=""):
    return _text(x, y, value, size, fill, 400, "mono",
                 f'letter-spacing="1.5" {extra}')


def _start(height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" '
        f'height="{height}" viewBox="0 0 1200 {height}" '
        'role="img" aria-labelledby="title desc">',
        f'<title id="title">{_e(title)}</title>',
        f'<desc id="desc">{_e(description)}</desc>',
        '<defs>',
        '<linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#101b2b"/><stop offset=".65" stop-color="#080d17"/>'
        '<stop offset="1" stop-color="#111426"/></linearGradient>',
        '<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="{CYAN}"/><stop offset="1" stop-color="{LILAC}"/>'
        '</linearGradient>',
        '<radialGradient id="halo">'
        '<stop stop-color="#327c91" stop-opacity=".24"/>'
        '<stop offset="1" stop-color="#327c91" stop-opacity="0"/>'
        '</radialGradient>',
        '<pattern id="grain" width="28" height="28" patternUnits="userSpaceOnUse">'
        '<circle cx="1" cy="1" r=".6" fill="#adc9e3" opacity=".1"/></pattern>',
        '</defs>',
        '<style>'
        '@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}'
        '@keyframes travel{to{stroke-dashoffset:-120}}'
        '@keyframes breathe{0%,100%{opacity:.4}50%{opacity:1}}'
        '@keyframes wave{0%,100%{opacity:.12}50%{opacity:.5}}'
        '.float{animation:float 9s ease-in-out infinite}'
        '.orbit{animation:travel 18s linear infinite}'
        '.beacon{animation:breathe 4s ease-in-out infinite}'
        '.city-glow{animation:wave 7s ease-in-out infinite}'
        '@media(prefers-reduced-motion:reduce){'
        '.float,.orbit,.beacon,.city-glow{animation:none!important}}'
        '</style>',
        f'<rect width="1200" height="{height}" rx="20" fill="{INK}"/>',
        f'<rect x=".5" y=".5" width="1199" height="{height-1}" rx="19.5" '
        f'fill="url(#surface)" stroke="{LINE}"/>',
        f'<rect x="1" y="1" width="1198" height="{height-2}" rx="19" '
        'fill="url(#grain)"/>',
    ]


def _end(parts):
    return "\n".join(parts + ["</svg>"]) + "\n"


def _iso_torus(cx, cy):
    """Painter-sorted shaded wire mesh, projected from a real 3D torus."""
    def point(u, v):
        x = (114 + 42 * math.cos(v)) * math.cos(u)
        y = (114 + 42 * math.cos(v)) * math.sin(u)
        z = 42 * math.sin(v)
        # Fixed camera rotation preserves dimensionality without scripting.
        a, b, c = 1.02, -.47, -.42
        y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
        x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
        x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
        perspective = 580 / (580 - z)
        return cx + x * perspective, cy + y * perspective, z

    faces = []
    rows, columns = 56, 16
    for i in range(rows):
        for j in range(columns):
            corners = [point(2 * math.pi * u / rows, 2 * math.pi * v / columns)
                       for u, v in ((i, j), (i+1, j), (i+1, j+1), (i, j+1))]
            depth = sum(p[2] for p in corners) / 4
            faces.append((depth, corners))
    result = ['<g class="float" stroke-linejoin="round">']
    for depth, corners in sorted(faces, key=lambda face: face[0]):
        light = max(0, min(1, (depth + 145) / 290))
        color = CYAN if depth > -8 else LILAC
        result.append(
            f'<polygon points="{" ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in corners)}" '
            f'fill="#0b1723" fill-opacity=".86" stroke="{color}" '
            f'stroke-opacity="{.10+.65*light:.2f}" stroke-width=".8"/>')
    result.append('</g>')
    return result


def render_hero(config):
    name = config.get("name", "Gokulakrishnan K")
    username = config.get("username", "Gokulakrishnan610")
    parts = _start(570, f"{name} — Software engineering, AI systems, full stack",
                   f"{name}, @{username}. Chennai, India. REC Computer Science, class of 2027. "
                   "An original animated 3D wireframe torus floats above a perspective grid.")
    parts += [
        '<ellipse cx="927" cy="253" rx="268" ry="241" fill="url(#halo)"/>',
        f'<path d="M36 68H1164" stroke="{LINE}"/>',
        '<path d="M37 29v19h19v-7H45v-5h11v-7z" fill="url(#accent)"/>',
        _label(70, 43, "GOKULAKRISHNAN / ENGINEER", WHITE),
        _label(1164, 43, "CHENNAI, INDIA  ·  13.08° N / 80.27° E", size=10,
               extra='text-anchor="end"'),
        _label(42, 113, "IDEA → SYSTEM → IMPACT", CYAN, 11),
        _text(35, 218, "GOKUL", 108, WHITE, 800, extra='letter-spacing="-5"'),
        _text(37, 304, "AKRISHNAN", 85, WHITE, 800, extra='letter-spacing="-4"'),
        '<rect x="42" y="330" width="46" height="3" rx="1.5" fill="url(#accent)"/>',
        _text(42, 373, "Building intelligence into", 29, MUTED, 400),
        _text(42, 411, "products that people use.", 29, WHITE, 600),
        '<path d="M740 141h23M740 141v23M1128 141h-23M1128 141v23'
        'M740 403h23M740 403v-23M1128 403h-23M1128 403v-23" '
        f'fill="none" stroke="{LINE}"/>',
        '<ellipse cx="930" cy="254" rx="214" ry="70" transform="rotate(-28 930 254)" '
        'fill="none" stroke="#385465" stroke-width=".9"/>',
        '<ellipse class="orbit" cx="930" cy="254" rx="214" ry="70" '
        'transform="rotate(-28 930 254)" fill="none" stroke="#6ce5e8" '
        'stroke-width="1.7" stroke-dasharray="8 112" opacity=".8"/>',
    ]
    # Low perspective grid; all lines remain behind the sculpture.
    for x in range(700, 1201, 50):
        parts.append(f'<path d="M930 306L{x} 437" stroke="#264251" stroke-opacity=".36"/>')
    for y in (345, 357, 374, 399, 432):
        ratio = (y - 306) / 131
        parts.append(f'<path d="M{930-230*ratio:.1f} {y}H{930+271*ratio:.1f}" '
                     'stroke="#264251" stroke-opacity=".36"/>')
    parts += _iso_torus(928, 250)
    parts += [
        '<circle class="beacon" cx="1083" cy="158" r="4" fill="#d0ed88"/>',
        '<circle cx="1083" cy="158" r="10" stroke="#d0ed88" fill="none" opacity=".2"/>',
        _label(931, 451, "CONTINUOUSLY BUILDING", CYAN, 9, 'text-anchor="middle"'),
        f'<path d="M36 479H1164" stroke="{LINE}"/>',
    ]
    pills = [(42, 190, "SOFTWARE ENGINEERING"), (244, 127, "AI SYSTEMS"), (383, 126, "FULL STACK")]
    for x, width, label in pills:
        parts += [f'<rect x="{x}" y="502" width="{width}" height="30" rx="15" '
                  'fill="#101e2b" stroke="#2b4351"/>',
                  _label(x + width/2, 521, label, WHITE, 9, 'text-anchor="middle"')]
    parts += [_label(1162, 516, "REC · COMPUTER SCIENCE '27", size=10,
                     extra='text-anchor="end"'),
              _text(1162, 538, f"@{username}", 12, MUTED, family="mono",
                    extra='text-anchor="end"')]
    return _end(parts)


def _calendar(snapshot):
    calendar = snapshot.get("contributions") or {}
    unique = {}
    for entry in calendar.get("days", []):
        try:
            day = date.fromisoformat(entry["date"])
        except (KeyError, TypeError, ValueError):
            continue
        unique[day] = {"date": day, "count": _number(entry.get("count")),
                       "level": min(4, _number(entry.get("level")))}
    return [unique[key] for key in sorted(unique)]


def _updated(snapshot):
    raw = snapshot.get("updated_at", "")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y · %H:%M UTC")
    except (ValueError, TypeError, AttributeError):
        return "Update time unavailable"


def render_dashboard(snapshot):
    repos = [repo for repo in snapshot.get("repos", []) if not repo.get("fork", False)]
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    stars = sum(_number(repo.get("stargazers_count")) for repo in repos)
    followers = _number((snapshot.get("user") or {}).get("followers"))
    parts = _start(390, "GitHub pulse — repository and contribution snapshot",
                   f"{len(repos)} public non-fork repositories, {stars} stars received across "
                   f"those repositories, and {followers} followers. "
                   + (f"{total} contributions in the returned calendar. " if days else
                      "Contribution calendar unavailable. ")
                   + "Language mix counts each repository's primary language once; "
                   "it does not measure code volume or proficiency.")
    parts += [_label(36, 39, "01 / GITHUB PULSE", CYAN),
              _label(1164, 39, f"SNAPSHOT · {_updated(snapshot)}", size=10,
                     extra='text-anchor="end"'),
              f'<path d="M36 61H1164" stroke="{LINE}"/>']
    stats = [(len(repos), "PUBLIC REPOSITORIES", "owned · forks excluded", CYAN),
             (stars, "STARS RECEIVED", "across owned repositories", LILAC),
             (followers, "FOLLOWERS", "people following the work", LIME),
             (total if days else None, "CONTRIBUTIONS", "returned calendar window", "#78a9fa")]
    for index, (value, label, caption, color) in enumerate(stats):
        x = 36 + index * 282
        if index:
            parts.append(f'<path d="M{x-15} 89V182" stroke="{LINE}"/>')
        parts += [f'<circle cx="{x+4}" cy="88" r="3" fill="{color}"/>',
                  _text(x, 143, f"{value:,}" if value is not None else "—", 51, WHITE, 600,
                        extra='letter-spacing="-2"'),
                  _label(x, 168, label, color, 10),
                  _text(x, 189, caption, 12, MUTED)]
    parts += [f'<path d="M36 216H1164" stroke="{LINE}"/>',
              _label(36, 249, "LANGUAGE MIX", WHITE, 11),
              _text(1164, 249, "Primary language · repository counts", 12, MUTED,
                    extra='text-anchor="end"')]
    languages = Counter(repo.get("language") or "Unspecified" for repo in repos)
    ranked = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(amount for _, amount in ranked[5:]))]
    if ranked:
        x = 36.0
        for index, (_, count) in enumerate(ranked):
            width = 1128 * count / len(repos)
            parts.append(f'<rect x="{x:.2f}" y="271" width="{max(.1, width-3):.2f}" '
                         f'height="15" rx="3" fill="{PALETTE[index]}"/>')
            x += width
        # Single row has six deliberately bounded labels at most.
        for index, (language, count) in enumerate(ranked):
            x = 36 + index * 190
            display = language if len(language) <= 16 else language[:15] + "…"
            parts += [f'<circle cx="{x+4}" cy="314" r="4" fill="{PALETTE[index]}"/>',
                      _text(x+15, 319, f"{display}  {count}", 12, WHITE)]
    else:
        parts.append(_text(36, 283, "No public repository language data available.", 14, MUTED))
    parts += [_text(36, 363, "Each public, non-fork repository counts once. Language mix is not a skill rating.",
                    11, MUTED, family="mono"),
              '<path d="M1130 351l12 12 22-22" stroke="#6ce5e8" stroke-width="1.5" fill="none"/>']
    return _end(parts)


def _polygon(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in points)}" fill="{fill}" {extra}/>'


def render_contributions(snapshot):
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max((day["count"] for day in days), default=0)
    parts = _start(575, "Contribution city — one building for each calendar day",
                   (f"{total} contributions over {len(days)} calendar days; {active} active days; "
                    f"best day {best} contributions. Each building is a day. "
                    "Height uses a capped logarithmic scale; color follows GitHub contribution levels. "
                    "Exact date and count appear in every building's title."
                    if days else "Contribution calendar data is unavailable."))
    parts += [_label(36, 39, "02 / CONTRIBUTION CITY", CYAN),
              _label(1164, 39, "ONE DAY. ONE BUILDING.", size=10,
                     extra='text-anchor="end"'),
              _text(34, 99, "A YEAR IN MOTION.", 43, WHITE, 700,
                    extra='letter-spacing="-1.8"')]
    if not days:
        parts += [_text(36, 182, "The city is waiting for contribution data.", 25, WHITE),
                  _text(36, 215, "A successful profile refresh will build it from the actual calendar.", 17, MUTED),
                  f'<path d="M36 490H1164" stroke="{LINE}"/>',
                  _label(36, 535, "CALENDAR UNAVAILABLE · NO ESTIMATED COUNTS", MUTED)]
        return _end(parts)

    for x, amount, label, color in [(802, total, "CONTRIBUTIONS", CYAN),
                                     (964, active, "ACTIVE DAYS", LILAC),
                                     (1108, best, "BEST DAY", LIME)]:
        parts += [_text(x, 91, f"{amount:,}", 31, WHITE, 600,
                        extra='text-anchor="middle" letter-spacing="-1"'),
                  _label(x, 115, label, color, 8.5, 'text-anchor="middle"')]
    parts.append(_text(36, 133, "A living skyline, built from the days the work happened.", 15, MUTED))

    # Calendar placement uses actual dates, preserving missing days as gaps.
    first, last = days[0]["date"], days[-1]["date"]
    sunday_offset = (first.weekday() + 1) % 7
    slots = (last-first).days + sunday_offset + 1
    weeks = max(1, (slots+6)//7)
    step_x = min(17.1, 906/max(1, weeks-1))
    step_y = min(2.6, 138/max(1, weeks-1))
    dx, dy = min(7.5, step_x*.44), 4.25
    origin_x, origin_y = 179, 281
    end_x = origin_x + (weeks-1)*step_x
    end_y = origin_y + (weeks-1)*step_y
    # A shallow floating plinth grounds the skyline.
    platform = [(origin_x-10, origin_y-7), (end_x+15, end_y-7),
                (end_x-72, end_y+65), (origin_x-97, origin_y+65)]
    parts += [_polygon([(x, y+10) for x, y in platform], "#040913"),
              _polygon(platform, "#0d1724", 'stroke="#2c4355" stroke-width=".8"')]
    for weekday in range(7):
        x = origin_x-weekday*12.5
        y = origin_y+weekday*8.6
        parts.append(f'<path d="M{x:.1f} {y:.1f}l{(weeks-1)*step_x:.1f} {(weeks-1)*step_y:.1f}" '
                     'stroke="#31495b" stroke-opacity=".32" stroke-width=".5"/>')
    columns = []
    for day in days:
        offset = (day["date"]-first).days+sunday_offset
        week, weekday = divmod(offset, 7)
        x = origin_x+week*step_x-weekday*12.5
        y = origin_y+week*step_y+weekday*8.6
        count = day["count"]
        height = 2 if not count else min(91, 9+math.log2(count+1)*11)
        columns.append((y, x, height, day))
    # Depth sorting allows tall buildings to occlude farther neighbors naturally.
    colors = ["#23364a", "#285f6a", "#398e94", "#56c5c7", CYAN]
    for y, x, height, day in sorted(columns, key=lambda cell: (cell[0], cell[1])):
        count, level = day["count"], day["level"]
        if count and level == 0:
            level = 1
        top = colors[level]
        west = [(x-dx,y), (x,y+dy), (x,y+dy-height), (x-dx,y-height)]
        east = [(x,y+dy), (x+dx,y), (x+dx,y-height), (x,y+dy-height)]
        roof = [(x,y-dy-height),(x+dx,y-height),(x,y+dy-height),(x-dx,y-height)]
        parts += ['<g>',
                  f'<title>{day["date"].isoformat()}: {count:,} contribution{"s" if count != 1 else ""}</title>',
                  _polygon(west, top, 'fill-opacity=".36"'),
                  _polygon(east, top, 'fill-opacity=".60"'),
                  _polygon(roof, top, 'stroke="#080d17" stroke-width=".45"')]
        if count:
            parts.append(f'<path d="M{x:.2f} {y+dy:.2f}V{y+dy-height:.2f}" '
                         f'stroke="{top}" stroke-opacity=".4" stroke-width=".45"/>')
        if level == 4:
            parts.append(_polygon(roof, "#efffff", f'class="city-glow" opacity=".12" '
                                  f'style="animation-delay:-{(day["date"].toordinal()%14)/2}s"'))
        parts.append('</g>')
    parts += [_label(82, 397, "SUN → SAT", MUTED, 8,
                     extra='transform="rotate(90 82 397)"'),
              _label(182, 480, first.strftime("%d %b %Y").upper(), MUTED, 10),
              _label(1110, 480, last.strftime("%d %b %Y").upper(), MUTED, 10,
                     extra='text-anchor="end"'),
              '<path d="M350 476H929m-7-4 7 4-7 4" fill="none" stroke="#3a5568"/>',
              f'<path d="M36 502H1164" stroke="{LINE}"/>',
              _text(36, 530, "Height follows a capped log₂ scale. Color follows GitHub activity levels.", 11, MUTED,
                    family="mono"),
              _text(36, 551, f"{len(days)} dated cells · GitHub calendar · refreshed {_updated(snapshot)}", 10, MUTED,
                    family="mono"),
              _label(944, 537, "LESS", MUTED, 8)]
    for i, color in enumerate(colors):
        parts.append(f'<rect x="{984+i*21}" y="525" width="15" height="15" rx="3" fill="{color}"/>')
    parts.append(_label(1100, 537, "MORE", MUTED, 8))
    return _end(parts)


def render_footer(config):
    username = config.get("username", "Gokulakrishnan610")
    parts = _start(185, "Code. Create. Ship.",
                   f"{config.get('name', 'Gokulakrishnan K')} — {username}. Code. Create. Ship.")
    parts += [
        '<ellipse cx="1080" cy="90" rx="248" ry="166" fill="url(#halo)"/>',
        _label(36, 40, "ALWAYS A WORK IN PROGRESS", CYAN, 10),
        _text(34, 109, "Code. Create. Ship.", 54, WHITE, 700, extra='letter-spacing="-2"'),
        _text(37, 146, "Curiosity starts it. Craft makes it real.", 17, MUTED),
        '<g fill="none" stroke="#6ce5e8" stroke-width="1.1">'
        '<path d="M970 35l104 60-104 60-104-60z" opacity=".20"/>'
        '<path d="M1000 35l104 60-104 60-104-60z" opacity=".35"/>'
        '<path d="M1030 35l104 60-104 60-104-60z" opacity=".60"/>'
        '<path class="orbit" d="M1060 35l104 60-104 60-104-60z" '
        'stroke-dasharray="8 12" opacity=".9"/></g>',
        '<circle class="beacon" cx="1060" cy="95" r="5" fill="#d0ed88"/>',
    ]
    return _end(parts)
