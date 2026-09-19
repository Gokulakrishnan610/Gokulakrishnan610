"""Editorial hero and footer artwork for the GitHub profile."""

from html import escape


PAPER = "#f2efe8"
INK = "#171716"
MUTED = "#66645f"
ORANGE = "#ff5a36"
BLUE = "#3157d5"
RULE = "#c9c5bb"


def _e(value):
    return escape(str(value), quote=True)


def _text(x, y, value, size=16, fill=INK, weight=400, extra=""):
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        'font-family="Arial,Helvetica,sans-serif" '
        f'font-weight="{weight}" {extra}>{_e(value)}</text>'
    )


def _mono(x, y, value, size=12, fill=MUTED, extra=""):
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        "font-family=\"'SFMono-Regular',Consolas,'Liberation Mono',monospace\" "
        f'letter-spacing="1.2" {extra}>{_e(value)}</text>'
    )


def _start(height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" '
        f'viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{_e(title)}</title>',
        f'<desc id="desc">{_e(description)}</desc>',
        '<style>'
        '@keyframes slide{0%,15%{transform:translateX(0)}85%,100%{transform:translateX(112px)}}'
        '@keyframes sweep{0%,12%{transform:translateX(0)}88%,100%{transform:translateX(842px)}}'
        '@keyframes rise{0%,12%{transform:translateY(0)}88%,100%{transform:translateY(174px)}}'
        '@keyframes blink{0%,45%{opacity:1}50%,100%{opacity:.18}}'
        '.slide{animation:slide 8s cubic-bezier(.65,0,.35,1) infinite alternate}'
        '.sweep{animation:sweep 10s cubic-bezier(.65,0,.35,1) infinite alternate}'
        '.rise{animation:rise 7s cubic-bezier(.65,0,.35,1) infinite alternate}'
        '.blink{animation:blink 2.4s steps(1,end) infinite}'
        '@media(prefers-reduced-motion:reduce){.slide,.sweep,.rise,.blink{animation:none!important}}'
        '</style>',
        f'<rect width="1200" height="{height}" rx="16" fill="{PAPER}"/>',
    ]


def _end(parts):
    return "\n".join(parts + ["</svg>"]) + "\n"


def render_hero(config):
    name = config.get("name", "Gokulakrishnan K")
    username = config.get("username", "Gokulakrishnan610")
    parts = _start(
        480,
        f"{name} — software engineer",
        f"Editorial profile header for {name}, @{username}. Software engineer building AI, web, and connected systems in Chennai.",
    )
    parts += [
        f'<rect x="0" y="0" width="18" height="480" fill="{ORANGE}"/>',
        f'<path d="M58 62H1142" stroke="{RULE}"/>',
        _mono(58, 42, "GOKULAKRISHNAN K / PORTFOLIO", 11, INK),
        _mono(1142, 42, "CHENNAI · INDIA", 11, INK, 'text-anchor="end"'),
        _text(54, 185, "GOKULAKRISHNAN", 94, INK, 800, 'letter-spacing="-5"'),
        f'<rect x="1050" y="102" width="92" height="92" fill="{ORANGE}"/>',
        _text(1096, 170, "K", 60, PAPER, 800, 'text-anchor="middle"'),
        f'<path d="M58 222H1142" stroke="{INK}" stroke-width="2"/>',
        f'<rect x="58" y="252" width="490" height="88" fill="{BLUE}"/>',
        _text(78, 307, "SOFTWARE ENGINEER & BUILDER", 23, PAPER, 700),
        _text(600, 280, "Building useful systems across", 24, INK, 600),
        _text(600, 316, "AI, web, and connected devices.", 24, INK, 600),
        f'<path d="M58 370H1142" stroke="{RULE}" stroke-width="4"/>',
        f'<rect class="sweep" x="58" y="363" width="184" height="14" fill="{ORANGE}"/>',
        _text(58, 414, "AI agents", 20, INK, 600),
        _text(245, 414, "Full-stack products", 20, INK, 600),
        _text(520, 414, "Connected devices", 20, INK, 600),
        _text(800, 414, "Community building", 20, INK, 600),
        f'<circle class="blink" cx="225" cy="407" r="5" fill="{ORANGE}"/>',
        f'<circle class="blink" cx="500" cy="407" r="5" fill="{ORANGE}" style="animation-delay:-.6s"/>',
        f'<circle class="blink" cx="780" cy="407" r="5" fill="{ORANGE}" style="animation-delay:-1.2s"/>',
        f'<path d="M58 425H1142" stroke="{RULE}"/>',
        _mono(58, 456, "REC · COMPUTER SCIENCE · CLASS OF 2027", 11),
        _mono(1142, 456, f"@{username}", 11, extra='text-anchor="end"'),
    ]
    return _end(parts)


def render_footer(config):
    name = config.get("name", "Gokulakrishnan K")
    username = config.get("username", "Gokulakrishnan610")
    parts = _start(
        250,
        f"Contact {name}",
        f"Editorial footer for {name}, @{username}, with portfolio and location details.",
    )
    parts += [
        f'<rect x="0" y="0" width="18" height="250" fill="{BLUE}"/>',
        f'<rect class="rise" x="5" y="18" width="8" height="42" fill="{PAPER}"/>',
        _mono(58, 42, "LET'S WORK TOGETHER", 11, INK),
        _text(56, 105, "gokulakrishnank.in", 58, INK, 700, 'letter-spacing="-2.5"'),
        _text(58, 151, "just a CS kid turning caffeine, curiosity & code into things people actually use", 22, INK, 500),
        f'<path d="M58 183H1142" stroke="{RULE}" stroke-width="4"/>',
        f'<rect class="sweep" x="58" y="176" width="184" height="14" fill="{ORANGE}"/>',
        _mono(58, 224, "GOKULAKRISHNAN K", 11),
        _mono(600, 224, "SOFTWARE · AI · SYSTEMS", 11, extra='text-anchor="middle"'),
        _mono(1142, 224, "CHENNAI, INDIA  ↗", 11, extra='text-anchor="end"'),
    ]
    return _end(parts)
