"""Preserved hero and footer artwork, with self-contained accessible animation."""

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
