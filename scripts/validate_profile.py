#!/usr/bin/env python3
"""Check local README links, accessible artwork, and self-contained SVG assets.

This is an offline build check, not a sanitizer for arbitrary uploaded SVGs.
Reproducibility is checked separately by generate_profile.py --check.
"""

from __future__ import annotations

import argparse
import base64
import binascii
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"
MAIN_VISUALS = {"dashboard.svg", "contributions.svg"}


class ReadmeLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ("src", "href"):
            if attrs.get(name):
                self.links.append(attrs[name])
        if attrs.get("srcset"):
            # The profile uses file/HTTPS candidates, never comma-containing data URIs.
            self.links.extend(candidate.strip().split()[0]
                              for candidate in attrs["srcset"].split(",") if candidate.strip())
        if tag == "img" and not attrs.get("alt", "").strip():
            self.errors.append("README image is missing descriptive alt text")


def validate_readme(root: Path) -> list[str]:
    readme = root / "README.md"
    if not readme.is_file():
        return ["README.md is missing"]
    text = readme.read_text(encoding="utf-8")
    parser = ReadmeLinks()
    parser.feed(text)
    errors = parser.errors
    if re.search(r"\{\{[^{}\n]+\}\}", text):
        errors.append("README contains an unresolved template variable")
    # Inline Markdown destinations, including angle-bracketed paths with spaces.
    for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", text):
        parser.links.append(match[1] or match[2])
    # Reference-style Markdown link definitions.
    for match in re.finditer(r"^\s{0,3}\[[^\]\n]+\]:\s*(?:<([^>]+)>|(\S+))", text, re.M):
        parser.links.append(match[1] or match[2])
    root = root.resolve()
    for link in sorted(set(parser.links)):
        parts = urlsplit(link)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        destination = (root / unquote(parts.path).lstrip("/")).resolve()
        if not destination.is_relative_to(root):
            errors.append(f"README link escapes the repository: {link}")
        elif not destination.exists():
            errors.append(f"README local link does not exist: {link}")
    return errors


def _check_css(css: str, label: str) -> list[str]:
    errors = []
    if re.search(r"@import\b|expression\s*\(|(?:-moz-binding|behavior)\s*:", css, re.I):
        errors.append(f"{label}: unsafe or external CSS")
    for match in re.finditer(r"url\s*\(\s*(['\"]?)(.*?)\1\s*\)", css, re.I | re.S):
        if not match[2].strip().startswith("#"):
            errors.append(f"{label}: SVG must not load external CSS resources")
    return errors


def validate_svg(path: Path, *, accessible: bool = False) -> list[str]:
    label = path.name
    text = path.read_text(encoding="utf-8")
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.I):
        return [f"{label}: SVG must not declare a DTD or entities"]
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        return [f"{label}: invalid XML: {error}"]
    if root.tag != SVG + "svg":
        return [f"{label}: expected an SVG root element and namespace"]
    errors = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"script", "foreignobject", "iframe", "object", "embed"}:
            errors.append(f"{label}: unsafe SVG element {tag}")
        if tag == "style":
            errors.extend(_check_css("".join(element.itertext()), label))
        for key, value in element.attrib.items():
            name = key.rsplit("}", 1)[-1].lower()
            if name.startswith("on"):
                errors.append(f"{label}: event-handler attributes are forbidden")
            if name in {"href", "src"} and value and not value.startswith("#"):
                # Pac-Man's ghost sprites are embedded PNGs, not network resources.
                embedded_png = False
                if tag == "image" and value.startswith("data:image/png;base64,"):
                    try:
                        data = base64.b64decode(value.split(",", 1)[1], validate=True)
                        embedded_png = data.startswith(b"\x89PNG\r\n\x1a\n")
                    except (ValueError, binascii.Error):
                        pass
                if not embedded_png:
                    errors.append(f"{label}: SVG must not reference external resources")
            if name == "attributename" and value.lower() in {"href", "xlink:href", "src"}:
                errors.append(f"{label}: SVG must not animate resource references")
            errors.extend(_check_css(value, label))
    if accessible:
        labels = set(root.get("aria-labelledby", "").split())
        for tag in ("title", "desc"):
            element = root.find(SVG + tag)
            if element is None or not "".join(element.itertext()).strip():
                errors.append(f"{label}: main visual needs a nonempty {tag}")
            elif element.get("id") not in labels:
                errors.append(f"{label}: aria-labelledby must reference the {tag}")
        if root.get("role") != "img":
            errors.append(f"{label}: main visual needs role=img")
    return errors


def validate_repository(root: Path) -> list[str]:
    errors = validate_readme(root)
    for name in sorted(MAIN_VISUALS):
        if not (root / "assets" / name).is_file():
            errors.append(f"Missing main visual: assets/{name}")
    for path in sorted((root / "assets").rglob("*.svg")):
        errors.extend(validate_svg(path, accessible=path.name in MAIN_VISUALS))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Profile repository to validate")
    args = parser.parse_args()
    try:
        errors = validate_repository(args.root.resolve())
    except (OSError, ValueError) as error:
        errors = [str(error)]
    if errors:
        print("Profile validation failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print("README local links and SVG safety/accessibility checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
