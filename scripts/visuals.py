"""Small, self-contained GitHub statistics and contribution SVGs.

All values come from the supplied snapshot. An absent calendar is never
shown as a zero calendar. The charts are static, including for viewers who
prefer reduced motion; the profile's separate contribution games provide motion.
"""

from collections import Counter
from datetime import date, datetime
from html import escape
import math


INK = "#0d1117"
WHITE = "#e6edf3"
MUTED = "#8b949e"
LINE = "#30363d"
GREENS = ["#21262d", "#0e4429", "#006d32", "#26a641", "#39d353"]
LANGUAGE_COLORS = {
    "Python": "#3572a5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Java": "#b07219", "HTML": "#e34c26", "CSS": "#563d7c",
    "C": "#555555", "C++": "#f34b7d", "Jupyter Notebook": "#da5b0b",
    "Dart": "#00b4ab", "Shell": "#89e051", "Unspecified": "#484f58",
    "Other": "#8b949e",
}


def _e(value):
    return escape(str(value), quote=True)


def _number(value):
    try:
        return max(0, int(value))
    except (ValueError, TypeError, OverflowError):
        return 0


def _text(x, y, value, size=16, fill=WHITE, weight=400, extra=""):
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
        '<style>@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>',
        f'<rect x=".5" y=".5" width="1199" height="{height-1}" rx="6" '
        f'fill="{INK}" stroke="{LINE}"/>',
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
    parts = _start(199, "GitHub stats",
                   f"{len(repos)} public non-fork repositories, {stars} stars received across "
                   f"those repositories, and {followers} followers. "
                   + (f"{total} contributions in the returned calendar. " if days else
                      "Contribution calendar unavailable. ")
                   + "Language mix counts each repository's primary language once; "
                   "it does not measure code volume or proficiency.")
    parts += [_text(24, 33, "GitHub stats", 18, weight=600),
              _text(1176, 33, f"Updated {_updated(snapshot)}", 13, MUTED,
                    extra='text-anchor="end"')]
    stats = [(len(repos), "public repositories"), (stars, "stars"),
             (followers, "followers"), (total if days else None, "contributions")]
    for index, (value, label) in enumerate(stats):
        x = 24 + index * 288
        value_text = f"{value:,}" if value is not None else "—"
        parts.append(
            f'<text x="{x}" y="76" fill="{WHITE}" font-size="18" '
            'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
            f'<tspan font-weight="600">{value_text}</tspan>'
            f'<tspan dx="6" fill="{MUTED}" font-size="15">{_e(label)}</tspan></text>')
    languages = Counter(repo.get("language") or "Unspecified" for repo in repos)
    ranked = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(amount for _, amount in ranked[5:]))]
    if ranked:
        x = 24.0
        for language, count in ranked:
            width = 1152 * count / len(repos)
            color = LANGUAGE_COLORS.get(language, "#8b949e")
            parts.append(f'<rect x="{x:.2f}" y="104" width="{max(.1, width-2):.2f}" '
                         f'height="9" fill="{color}"/>')
            x += width
        for index, (language, count) in enumerate(ranked):
            x = 24 + index * 192
            color = LANGUAGE_COLORS.get(language, "#8b949e")
            display = language if len(language) <= 16 else language[:15] + "…"
            parts += [f'<circle cx="{x+4}" cy="139" r="4" fill="{color}"/>',
                      _text(x+15, 144, f"{display}  {count}", 13)]
    else:
        parts.append(_text(24, 126, "No public repository language data available.", 14, MUTED))
    parts.append(_text(24, 177, "Primary languages by repository count · forks excluded", 12, MUTED))
    return _end(parts)


def _polygon(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in points)}" fill="{fill}" {extra}/>'


def render_contributions(snapshot):
    days = _calendar(snapshot)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max((day["count"] for day in days), default=0)
    parts = _start(390 if days else 150, "Contributions",
                   (f"{total} contributions over {len(days)} calendar days; {active} active days; "
                    f"best day {best} contributions. Each column is a day. "
                    "Height uses a capped logarithmic scale; color follows GitHub contribution levels. "
                    "Exact date and count appear in every column's title."
                    if days else "Contribution calendar data is unavailable."))
    parts.append(_text(24, 33, "Contributions", 18, weight=600))
    if not days:
        parts.append(_text(24, 88, "Contribution calendar data is currently unavailable.", 16, MUTED))
        return _end(parts)

    first, last = days[0]["date"], days[-1]["date"]
    parts += [_text(1176, 33, f'{first.strftime("%d %b %Y")} – {last.strftime("%d %b %Y")}',
                    13, MUTED, extra='text-anchor="end"'),
              _text(24, 60, f"{total:,} contributions · {active} active days", 14, MUTED)]

    # Actual dates determine placement. Missing days remain gaps.
    sunday_offset = (first.weekday() + 1) % 7
    slots = (last-first).days + sunday_offset + 1
    weeks = max(1, (slots+6)//7)
    step_x = min(17.1, 906/max(1, weeks-1))
    step_y = min(2.15, 114/max(1, weeks-1))
    dx, dy = min(7.5, step_x*.44), 4.25
    origin_x, origin_y = 179, 161
    end_x = origin_x + (weeks-1)*step_x
    end_y = origin_y + (weeks-1)*step_y
    platform = [(origin_x-10, origin_y-7), (end_x+15, end_y-7),
                (end_x-72, end_y+65), (origin_x-97, origin_y+65)]
    parts.append(_polygon(platform, "#161b22", f'stroke="{LINE}" stroke-width=".8"'))
    for weekday in range(7):
        x = origin_x-weekday*12.5
        y = origin_y+weekday*8.6
        parts.append(f'<path d="M{x:.1f} {y:.1f}l{(weeks-1)*step_x:.1f} {(weeks-1)*step_y:.1f}" '
                     f'stroke="{LINE}" stroke-width=".5"/>')
    columns = []
    for day in days:
        offset = (day["date"]-first).days+sunday_offset
        week, weekday = divmod(offset, 7)
        x = origin_x+week*step_x-weekday*12.5
        y = origin_y+week*step_y+weekday*8.6
        count = day["count"]
        height = 2 if not count else min(91, 9+math.log2(count+1)*11)
        columns.append((y, x, height, day))
    # Draw distant columns first to preserve depth at intersecting edges.
    for y, x, height, day in sorted(columns, key=lambda cell: (cell[0], cell[1])):
        count, level = day["count"], day["level"]
        if count and level == 0:
            level = 1
        top = GREENS[level]
        west = [(x-dx,y), (x,y+dy), (x,y+dy-height), (x-dx,y-height)]
        east = [(x,y+dy), (x+dx,y), (x+dx,y-height), (x,y+dy-height)]
        roof = [(x,y-dy-height),(x+dx,y-height),(x,y+dy-height),(x-dx,y-height)]
        parts += ['<g>',
                  f'<title>{day["date"].isoformat()}: {count:,} contribution{"s" if count != 1 else ""}</title>',
                  _polygon(west, top, 'fill-opacity=".50"'),
                  _polygon(east, top, 'fill-opacity=".75"'),
                  _polygon(roof, top, f'stroke="{INK}" stroke-width=".45"'),
                  '</g>']
    parts += [_text(24, 369, "One column per day · height on a capped log scale", 12, MUTED),
              _text(983, 369, "Less", 12, MUTED, extra='text-anchor="end"')]
    for i, color in enumerate(GREENS):
        parts.append(f'<rect x="{995+i*24}" y="356" width="15" height="15" rx="2" fill="{color}"/>')
    parts.append(_text(1121, 369, "More", 12, MUTED))
    return _end(parts)
