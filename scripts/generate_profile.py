#!/usr/bin/env python3
"""Fetch public GitHub data, then deterministically render the profile. No packages required."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com"


def request(url: str, *, as_json: bool = True):
    """Retry transient failures; never send the Actions token to a non-API host."""
    headers = {"User-Agent": "Gokulakrishnan610-profile", "Accept": "application/vnd.github+json" if as_json else "text/html"}
    token = os.environ.get("GITHUB_TOKEN")
    if urlparse(url).hostname == "api.github.com":
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if token:
            headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                content = response.read().decode("utf-8")
            return json.loads(content) if as_json else content
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"GitHub request failed: HTTP {error.code} for {url}") from error
        except (URLError, TimeoutError) as error:
            if attempt == 2:
                raise RuntimeError(f"GitHub request failed after retries for {url}") from error
        time.sleep(2 ** attempt)
    raise RuntimeError("Unreachable request state")


class ContributionParser(HTMLParser):
    """Match dated calendar cells with their exact-count accessibility tooltips."""

    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.current_tooltip = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-date") and "data-level" in attrs:
            cell_id = attrs.get("id")
            if not cell_id or cell_id in self.cells:
                raise ValueError("Missing or duplicate contribution cell ID")
            self.cells[cell_id] = {"date": attrs["data-date"], "level": int(attrs["data-level"])}
        if tag == "tool-tip":
            self.current_tooltip = attrs.get("for")
            if self.current_tooltip:
                self.tooltips[self.current_tooltip] = ""

    def handle_data(self, text):
        if self.current_tooltip:
            self.tooltips[self.current_tooltip] += text

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.current_tooltip = None

    def days(self):
        result = []
        for cell_id, cell in self.cells.items():
            text = " ".join(self.tooltips.get(cell_id, "").split())
            match = re.match(r"^(No|\d{1,3}(?:,\d{3})+|\d+) contributions? on\b", text)
            if not match:
                raise ValueError(f"Contribution count missing for {cell['date']}; calendar format may have changed")
            count = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            result.append({**cell, "count": count})
        return sorted(result, key=lambda day: day["date"])


def integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f"Invalid non-negative integer: {label}")


def iso_time(value):
    if not isinstance(value, str):
        raise ValueError("Expected an ISO timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed


def validate_snapshot(snapshot, username):
    if snapshot.get("schema_version") != 1:
        raise ValueError("Unsupported snapshot schema")
    captured = iso_time(snapshot["updated_at"])
    user = snapshot["user"]
    if user["login"].lower() != username.lower():
        raise ValueError("Snapshot belongs to another GitHub user")
    for key in ("public_repos", "followers"):
        integer(user[key], key)
    repos = snapshot["repos"]
    if not isinstance(repos, list):
        raise ValueError("Repositories must be a list")
    names = set()
    for repo in repos:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo["name"]) or repo["name"].lower() in names:
            raise ValueError("Invalid or duplicate repository name")
        names.add(repo["name"].lower())
        if repo["html_url"] != f"https://github.com/{username}/{repo['name']}":
            raise ValueError("Unexpected repository URL")
        for key in ("stargazers_count", "forks_count"):
            integer(repo[key], key)
        for key in ("fork", "archived"):
            if type(repo[key]) is not bool:
                raise ValueError(f"Invalid repository {key}")
        if repo["language"] is not None and not isinstance(repo["language"], str):
            raise ValueError("Invalid repository language")
        if repo["pushed_at"]:
            iso_time(repo["pushed_at"])
    if len(repos) != user["public_repos"]:
        raise ValueError("Repository count changed during fetch or pagination is incomplete; rerun")
    days = snapshot["contributions"]["days"]
    if not isinstance(days, list) or not 350 <= len(days) <= 378:
        raise ValueError("Expected a complete contribution calendar")
    previous = None
    for day in days:
        current = date.fromisoformat(day["date"])
        integer(day["count"], "contribution count")
        integer(day["level"], "contribution level")
        if day["level"] > 4 or (day["count"] == 0) != (day["level"] == 0):
            raise ValueError("Contribution count and intensity disagree")
        if previous and (current - previous).days != 1:
            raise ValueError("Contribution dates must be unique, sorted, and contiguous")
        if current > captured.date():
            raise ValueError("Contribution date is in the future")
        previous = current
    if abs((captured.date() - previous).days) > 1:
        raise ValueError("Contribution calendar is stale relative to snapshot")
    if not isinstance(snapshot["events"], list):
        raise ValueError("Events must be a list")
    for event in snapshot["events"]:
        iso_time(event["created_at"])
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", event["repo"]):
            raise ValueError("Invalid event repository")
        if not isinstance(event["type"], str):
            raise ValueError("Invalid event type")


def fetch_snapshot(username):
    user = request(f"{API}/users/{quote(username)}")
    if not isinstance(user, dict) or "login" not in user:
        raise ValueError("GitHub profile response is invalid")
    repos = []
    for page in range(1, 101):
        batch = request(f"{API}/users/{quote(username)}/repos?type=owner&sort=full_name&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("GitHub repositories response is invalid")
        for repo in batch:
            if repo.get("private") is not False or repo.get("owner", {}).get("login", "").lower() != username.lower():
                raise ValueError("Repository endpoint returned unexpected ownership or visibility")
            repos.append({key: repo[key] for key in ("name", "html_url", "language", "stargazers_count", "forks_count", "fork", "archived", "pushed_at")})
        if len(batch) < 100:
            break
    else:
        raise ValueError("Repository pagination limit reached")
    raw_events = request(f"{API}/users/{quote(username)}/events/public?per_page=30")
    if not isinstance(raw_events, list):
        raise ValueError("GitHub events response is invalid")
    events = []
    for event in raw_events:
        if event.get("public") is not True:
            raise ValueError("Non-public event returned by public endpoint")
        events.append({"type": event["type"], "repo": event["repo"]["name"], "created_at": event["created_at"]})
    parser = ContributionParser()
    parser.feed(request(f"https://github.com/users/{quote(username)}/contributions", as_json=False))
    snapshot = {
        "schema_version": 1,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "user": {key: user[key] for key in ("login", "public_repos", "followers")},
        "repos": sorted(repos, key=lambda repo: repo["name"].lower()),
        "contributions": {"source": f"https://github.com/users/{username}/contributions", "days": parser.days()},
        "events": events,
    }
    validate_snapshot(snapshot, username)
    return snapshot


def project_table(config, snapshot):
    lookup = {repo["name"].lower(): repo for repo in snapshot["repos"]}
    projects = ['<table>', '<thead><tr><th align="left">Project</th><th align="left">What it does</th></tr></thead>', '<tbody>']
    for project in config["projects"]:
        repo = lookup.get(project["repo"].lower())
        if repo is None:
            raise ValueError(f"Featured project is not a public repository: {project['repo']}")
        projects.append(
            '<tr>\n'
            '<td width="30%" valign="top">'
            f'<strong><a href="{escape(repo["html_url"], quote=True)}">{escape(project["name"])} ↗</a></strong>'
            f'<br /><sub>{escape(project["category"])}</sub></td>\n'
            f'<td valign="top">{escape(project["description"])}'
            f'<br /><br /><sub>{escape(project["stack"])}</sub></td>\n'
            '</tr>'
        )
    return '\n'.join(projects + ['</tbody>', '</table>'])


def render_readme(config, snapshot, template):
    username = config["username"]
    original = [repo for repo in snapshot["repos"] if not repo["fork"]]
    recent = sorted((repo for repo in original if not repo["archived"] and repo["name"].lower() != username.lower() and repo["pushed_at"]), key=lambda repo: repo["pushed_at"], reverse=True)[:3]
    recent_text = "\n".join(f'- **[{repo["name"]}]({repo["html_url"]})** · {escape(repo["language"] or "Language not reported")} · pushed {repo["pushed_at"][:10]}' for repo in recent) or "No public repository pushes are available."
    event_labels = {"PushEvent": "Pushed code to", "CreateEvent": "Created a repository or ref in", "PullRequestEvent": "Updated a pull request in", "IssuesEvent": "Updated an issue in", "IssueCommentEvent": "Commented in", "ReleaseEvent": "Published a release in", "WatchEvent": "Starred", "ForkEvent": "Forked", "PullRequestReviewEvent": "Reviewed a pull request in", "DeleteEvent": "Deleted a ref in"}
    event_text = []
    seen = set()
    for event in sorted(snapshot["events"], key=lambda item: item["created_at"], reverse=True):
        repo, kind, day = event["repo"], event["type"], event["created_at"][:10]
        if repo.lower() == f"{username}/{username}".lower() or kind not in event_labels or (repo, kind, day) in seen:
            continue
        seen.add((repo, kind, day))
        event_text.append(f'- {day} · {event_labels[kind]} [{repo}](https://github.com/{repo})')
        if len(event_text) == 5:
            break
    days = snapshot["contributions"]["days"]
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    replacements = {
        "USERNAME": username,
        "EMAIL": config["email"],
        "LINKEDIN": config["linkedin"],
        "PORTFOLIO": config.get("portfolio", ""),
        "PROJECTS": project_table(config, snapshot),
        "RECENT_REPOS": recent_text,
        "RECENT_ACTIVITY": "\n".join(event_text) or "No recent public events were returned by GitHub. Repository push dates above remain available.",
        "METRICS_SUMMARY": f'**{len(original)} original public repositories** · **{sum(repo["stargazers_count"] for repo in original)} stars received** · **{snapshot["user"]["followers"]} followers**. Forks are excluded from repository, star, and language metrics. Language mix counts repositories by their primary language, not code volume or proficiency.',
        "CONTRIBUTION_SUMMARY": f'**{total:,} contributions** across **{active} active days** · {days[0]["date"]} → {days[-1]["date"]}. The calendar may include anonymized private contributions if enabled on GitHub; no private repository details are fetched.',
        "UPDATED_AT": iso_time(snapshot["updated_at"]).strftime("%d %b %Y, %H:%M UTC"),
    }
    for key, value in replacements.items():
        template = template.replace("{{" + key + "}}", value)
    if re.search(r"\{\{[A-Z_]+\}\}", template):
        raise ValueError("Unresolved README template variable")
    return template


def load_config():
    config = json.loads((ROOT / "profile-content/profile.json").read_text())
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", config["username"]):
        raise ValueError("Invalid GitHub username")
    if not re.fullmatch(r"[^\s<>\"@]+@[^\s<>\"@]+\.[^\s<>\"@]+", config["email"]):
        raise ValueError("Invalid email address")
    if not re.fullmatch(r"https://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?", config["linkedin"]):
        raise ValueError("Expected a LinkedIn profile URL")
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+/?", config["portfolio"]):
        raise ValueError("Expected an HTTPS portfolio domain")
    return config


def build_outputs(config, snapshot):
    from branding import render_hero, render_footer
    from visuals import render_achievements, render_dashboard, render_contributions

    template = (ROOT / "profile-content/README.template.md").read_text()
    outputs = {
        "README.md": render_readme(config, snapshot, template),
        "profile-content/snapshot.json": json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        "assets/hero.svg": render_hero(config),
        "assets/footer.svg": render_footer(config),
        "assets/achievements.svg": render_achievements(config),
        "assets/dashboard.svg": render_dashboard(snapshot),
        "assets/contributions.svg": render_contributions(snapshot),
    }
    for path, text in outputs.items():
        if path.endswith(".svg"):
            root = ET.fromstring(text)
            if root.tag != "{http://www.w3.org/2000/svg}svg":
                raise ValueError(f"Invalid SVG: {path}")
    return outputs


def write_outputs(outputs):
    # Prepare every file before replacing any existing output. Failed network/validation
    # calls never reach here, so a failed refresh leaves the previous snapshot intact.
    with tempfile.TemporaryDirectory(prefix="profile-build-") as folder:
        staging = Path(folder)
        for index, (path, content) in enumerate(outputs.items()):
            (staging / str(index)).write_text(content, encoding="utf-8")
        for index, path in enumerate(outputs):
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Stage on destination filesystem to preserve atomic replacement semantics.
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
                temp.write((staging / str(index)).read_bytes())
                temporary = Path(temp.name)
            temporary.chmod(0o644)
            os.replace(temporary, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="Fetch current public data before rendering")
    mode.add_argument("--check", action="store_true", help="Check that generated files match the saved snapshot")
    args = parser.parse_args()
    try:
        config = load_config()
        snapshot = fetch_snapshot(config["username"]) if args.refresh else json.loads((ROOT / "profile-content/snapshot.json").read_text())
        validate_snapshot(snapshot, config["username"])
        outputs = build_outputs(config, snapshot)
        if args.check:
            changed = [path for path, text in outputs.items() if not (ROOT / path).is_file() or (ROOT / path).read_text() != text]
            if changed:
                raise ValueError("Generated files out of date: " + ", ".join(changed))
            print("Generated assets and README match the saved snapshot.")
        else:
            write_outputs(outputs)
            print(f"Rendered {len(outputs)} files from snapshot {snapshot['updated_at']}.")
    except (KeyError, TypeError, ValueError, RuntimeError, OSError) as error:
        print(f"Profile generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
