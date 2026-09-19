"""Self-contained GitHub statistics and contribution SVGs.

All values come from the supplied snapshot. An absent calendar is never
shown as a zero calendar. The contribution chart has a complete static frame;
its subtle highlights respect the viewer's reduced-motion preference.
"""

from collections import Counter
from datetime import date, datetime
from html import escape
import math


INK = "#080d17"
WHITE = "#ecf4fb"
MUTED = "#a4b2c4"
CYAN = "#6ce5e8"
LILAC = "#baa2fa"
LINE = "#26364b"
LEVEL_COLORS = ["#26364b", "#285d6b", "#388a98", "#57bfc7", CYAN]
LANGUAGE_COLORS = {
    "Python": CYAN, "JavaScript": "#e8d894", "TypeScript": LILAC,
    "Java": "#8db9ef", "HTML": "#e8ae93", "CSS": "#cba8e8",
    "C": "#b4c8d5", "C++": "#e5a6c4", "Jupyter Notebook": "#e8b684",
    "Dart": "#89d8ce", "Shell": "#c4d999", "Kotlin": "#dab4ee",
    "Unspecified": "#697b95", "Other": "#9cacc0",
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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" '
        f'height="{height}" viewBox="0 0 1200 {height}" '
        'role="img" aria-labelledby="title desc">',
        f'<title id="title">{_e(title)}</title>',
        f'<desc id="desc">{_e(description)}</desc>',
        '<defs><linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#101a2a"/><stop offset=".58" stop-color="#080d17"/>'
        '<stop offset="1" stop-color="#101423"/></linearGradient></defs>',
        '<style>'
        '@keyframes highlight{0%,100%{opacity:.05}50%{opacity:.24}}'
        '.highlight{animation:highlight 8s ease-in-out infinite}'
        '@media(prefers-reduced-motion:reduce){*{animation:none!important}}'
        '</style>',
        f'<rect x=".75" y=".75" width="1198.5" height="{height-1.5}" rx="18" '
        f'fill="url(#surface)" stroke="{LINE}" stroke-width="1.5"/>',
    ]


def _end(parts):
    return "\n".join(parts + ["</svg>"]) + "\n"


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
        return parsed.strftime("%d %b %Y")
    except (ValueError, TypeError, AttributeError):
        return "Date unavailable"


def render_dashboard(snapshot):
    repos = [repo for repo in snapshot.get("repos", []) if not repo.get("fork", False)]
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    stars = sum(_number(repo.get("stargazers_count")) for repo in repos)
    followers = _number((snapshot.get("user") or {}).get("followers"))
    parts = _start(440, "GitHub activity",
                   f"{len(repos)} public non-fork repositories, {stars} stars received across "
                   f"those repositories, and {followers} followers. "
                   + (f"{total} contributions in the returned calendar. " if days else
                      "Contribution calendar unavailable. ")
                   + "Language mix counts each repository's primary language once; "
                   "it does not measure code volume or proficiency.")
    parts += [_text(44, 56, "GitHub activity", 30, weight=600),
              _text(1156, 56, f"Updated {_updated(snapshot)}", 20, MUTED,
                    extra='text-anchor="end"'),
              f'<path d="M44 81H1156" stroke="{LINE}"/>']
    stats = [(len(repos), "Repositories"), (stars, "Stars received"),
             (followers, "Followers"), (total if days else None, "Contributions")]
    for index, (value, label) in enumerate(stats):
        x = 44 + index * 284
        value_text = f"{value:,}" if value is not None else "—"
        if index:
            parts.append(f'<path d="M{x-22} 111V204" stroke="{LINE}"/>')
        parts += [_text(x, 163, value_text, 64, WHITE, 600,
                        extra='letter-spacing="-2"'),
                  _text(x, 205, label, 22, MUTED)]
    parts += [_text(44, 245, "Owned public repositories · forks excluded", 20, MUTED),
              f'<path d="M44 269H1156" stroke="{LINE}"/>',
              _text(44, 305, "Primary languages", 24, WHITE, 500),
              _text(1156, 305, "By repository count", 20, MUTED,
                    extra='text-anchor="end"')]
    languages = Counter(repo.get("language") or "Unspecified" for repo in repos)
    ranked = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(amount for _, amount in ranked[5:]))]
    if ranked:
        x = 44.0
        for language, count in ranked:
            width = 1112 * count / len(repos)
            color = LANGUAGE_COLORS.get(language, LILAC)
            parts.append(f'<rect x="{x:.2f}" y="326" width="{max(.1, width-3):.2f}" '
                         f'height="13" rx="3" fill="{color}"/>')
            x += width
        for index, (language, count) in enumerate(ranked):
            x = 44 + (index % 3) * 382
            y = 377 + (index // 3) * 38
            color = LANGUAGE_COLORS.get(language, LILAC)
            display = language if len(language) <= 24 else language[:23] + "…"
            parts += [f'<circle cx="{x+6}" cy="{y-7}" r="5" fill="{color}"/>',
                      _text(x+22, y, display, 21),
                      _text(x+348, y, count, 21, MUTED, extra='text-anchor="end"')]
    else:
        parts.append(_text(44, 381, "No public repository language data available.", 22, MUTED))
    return _end(parts)


def _polygon(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in points)}" fill="{fill}" {extra}/>'


def render_contributions(snapshot):
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max((day["count"] for day in days), default=0)
    parts = _start(600 if days else 210, "GitHub contributions in 3D",
                   (f"{total} contributions over {len(days)} calendar days; {active} active days; "
                    f"best day {best} contributions. Each column is a day. "
                    "Height uses a capped logarithmic scale; color follows GitHub contribution levels. "
                    "Exact date and count appear in every column's title."
                    if days else "Contribution calendar data is unavailable."))
    parts += [_text(44, 56, "Contributions", 30, weight=600),
              _text(1156, 56, f"Updated {_updated(snapshot)}", 20, MUTED,
                    extra='text-anchor="end"'),
              f'<path d="M44 81H1156" stroke="{LINE}"/>']
    if not days:
        parts.append(_text(44, 150, "Contribution calendar data is currently unavailable.", 22, MUTED))
        return _end(parts)

    first, last = days[0]["date"], days[-1]["date"]
    for x, value, label, color in [(44, total, "Contributions", CYAN),
                                   (426, active, "Active days", LILAC),
                                   (808, best, "Most in one day", WHITE)]:
        parts += [_text(x, 139, f"{value:,}", 40, color, 600),
                  _text(x, 173, label, 21, MUTED)]

    # Actual dates determine placement. Missing days remain gaps.
    sunday_offset = (first.weekday() + 1) % 7
    slots = (last-first).days + sunday_offset + 1
    weeks = max(1, (slots+6)//7)
    step_x = min(17.1, 906/max(1, weeks-1))
    step_y = min(2.15, 114/max(1, weeks-1))
    dx, dy = min(7.5, step_x*.44), 4.25
    origin_x, origin_y = 179, 308
    end_x = origin_x + (weeks-1)*step_x
    end_y = origin_y + (weeks-1)*step_y
    platform = [(origin_x-10, origin_y-7), (end_x+15, end_y-7),
                (end_x-72, end_y+65), (origin_x-97, origin_y+65)]
    parts += [_polygon([(x, y+10) for x, y in platform], "#040810"),
              _polygon(platform, "#111d2b", 'stroke="#32475d" stroke-width="1"')]
    for weekday in range(7):
        x = origin_x-weekday*12.5
        y = origin_y+weekday*8.6
        parts.append(f'<path d="M{x:.1f} {y:.1f}l{(weeks-1)*step_x:.1f} {(weeks-1)*step_y:.1f}" '
                     'stroke="#3a5066" stroke-opacity=".6" stroke-width=".6"/>')
    columns = []
    for day in days:
        offset = (day["date"]-first).days+sunday_offset
        week, weekday = divmod(offset, 7)
        x = origin_x+week*step_x-weekday*12.5
        y = origin_y+week*step_y+weekday*8.6
        count = day["count"]
        height = 2 if not count else min(102, 9+math.log2(count+1)*12)
        columns.append((y, x, height, day))
    # Draw distant columns first to preserve depth at intersecting edges.
    for y, x, height, day in sorted(columns, key=lambda cell: (cell[0], cell[1])):
        count, level = day["count"], day["level"]
        if count and level == 0:
            level = 1
        top = LEVEL_COLORS[level]
        west = [(x-dx,y), (x,y+dy), (x,y+dy-height), (x-dx,y-height)]
        east = [(x,y+dy), (x+dx,y), (x+dx,y-height), (x,y+dy-height)]
        roof = [(x,y-dy-height),(x+dx,y-height),(x,y+dy-height),(x-dx,y-height)]
        parts += ['<g>',
                  f'<title>{day["date"].isoformat()}: {count:,} contribution{"s" if count != 1 else ""}</title>',
                  _polygon(west, top, 'fill-opacity=".36"'),
                  _polygon(east, top, 'fill-opacity=".68"'),
                  _polygon(roof, top, f'stroke="{INK}" stroke-width=".5"')]
        if count:
            parts.append(f'<path d="M{x:.2f} {y+dy:.2f}V{y+dy-height:.2f}" '
                         f'stroke="{top}" stroke-opacity=".48" stroke-width=".6"/>')
        if level == 4:
            delay = (day["date"].toordinal() % 16) / 2
            parts.append(_polygon(roof, WHITE, f'class="highlight" opacity=".05" '
                                  f'style="animation-delay:-{delay}s"'))
        parts.append('</g>')
    parts += [_text(179, 516, first.strftime("%d %b %Y"), 20, MUTED),
              _text(1110, 516, last.strftime("%d %b %Y"), 20, MUTED,
                    extra='text-anchor="end"'),
              '<path d="M344 509H934m-7-4 7 4-7 4" fill="none" stroke="#435b70"/>',
              f'<path d="M44 539H1156" stroke="{LINE}"/>',
              _text(44, 577, "One column per day · capped logarithmic height", 20, MUTED),
              _text(922, 577, "Less", 20, MUTED, extra='text-anchor="end"')]
    for i, color in enumerate(LEVEL_COLORS):
        parts.append(f'<rect x="{940+i*27}" y="560" width="19" height="19" rx="3" fill="{color}"/>')
    parts.append(_text(1085, 577, "More", 20, MUTED))
    return _end(parts)
