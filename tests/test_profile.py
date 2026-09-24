"""Offline regression tests for public-data accuracy and safe profile generation."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from html import escape
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_profile as profile
import validate_profile as validator
import visuals

USERNAME = "ExampleDev"


def repository(index=0):
    name = f"project-{index:03d}"
    return {"name": name, "html_url": f"https://github.com/{USERNAME}/{name}",
            "language": "Python", "stargazers_count": index, "forks_count": 0,
            "fork": False, "archived": False, "pushed_at": "2026-09-17T10:00:00Z"}


def snapshot(end=date(2026, 9, 18), repo_count=1):
    return {
        "schema_version": 1,
        "updated_at": f"{end.isoformat()}T12:00:00Z",
        "user": {"login": USERNAME, "public_repos": repo_count, "followers": 7},
        "repos": [repository(index) for index in range(repo_count)],
        "contributions": {"source": f"https://github.com/users/{USERNAME}/contributions",
                          "days": [{"date": (end - timedelta(days=364 - index)).isoformat(),
                                    "count": 0 if index % 2 else index + 1,
                                    "level": 0 if index % 2 else 4}
                                   for index in range(365)]},
        "events": [{"created_at": "2026-09-17T10:00:00Z", "type": "PushEvent",
                    "repo": f"{USERNAME}/project-000"}],
    }


def calendar_html(days):
    return "".join(
        f'<td id="day-{index}" data-date="{day["date"]}" data-level="{day["level"]}"></td>'
        f'<tool-tip for="day-{index}">{day["count"]:,} contributions on a calendar day.</tool-tip>'
        for index, day in enumerate(days))


def config():
    return {"username": USERNAME, "email": "dev@example.com", "linkedin": "https://linkedin.com/in/example",
            "projects": [{"repo": "project-000", "name": "Example", "category": "AI",
                          "description": "A project", "stack": "Python"}]}


class ContributionParserTests(unittest.TestCase):
    def test_tooltips_provide_exact_counts_in_date_order(self):
        parser = profile.ContributionParser()
        parser.feed('<tool-tip for="high">1,234 contributions on May 3rd.</tool-tip>'
                    '<td id="high" data-date="2026-05-03" data-level="4"></td>'
                    '<td id="zero" data-date="2026-05-01" data-level="0"></td>'
                    '<tool-tip for="zero">No contributions on May 1st.</tool-tip>'
                    '<td id="one" data-date="2026-05-02" data-level="1"></td>'
                    '<tool-tip for="one">\n 1 <span>contribution</span> on May 2nd. </tool-tip>')
        self.assertEqual(parser.days(), [
            {"date": "2026-05-01", "level": 0, "count": 0},
            {"date": "2026-05-02", "level": 1, "count": 1},
            {"date": "2026-05-03", "level": 4, "count": 1234}])

    def test_missing_or_unrecognized_tooltips_fail_instead_of_estimating(self):
        for tooltip in ("", "Many contributions on May 1st.", "-1 contributions on May 1st.",
                        "1,2 contributions on May 1st.", "1,,234 contributions on May 1st."):
            with self.subTest(tooltip=tooltip):
                parser = profile.ContributionParser()
                parser.feed('<td id="a" data-date="2026-05-01" data-level="4"></td>'
                            f'<tool-tip for="a">{tooltip}</tool-tip>')
                with self.assertRaises(ValueError):
                    parser.days()

    def test_missing_or_duplicate_cell_ids_fail(self):
        for markup in ('<td data-date="2026-05-01" data-level="0"></td>',
                       '<td id="a" data-date="2026-05-01" data-level="0"></td>' * 2):
            with self.subTest(markup=markup), self.assertRaises(ValueError):
                profile.ContributionParser().feed(markup)


class SnapshotValidationTests(unittest.TestCase):
    def test_complete_calendar_and_case_insensitive_owner_are_valid(self):
        profile.validate_snapshot(snapshot(), USERNAME)
        data = snapshot()
        data["user"]["login"] = USERNAME.lower()
        profile.validate_snapshot(data, USERNAME)

    def test_bad_calendar_is_rejected(self):
        mutations = {
            "duplicate date": lambda days: days.__setitem__(100, dict(days[99])),
            "missing date": lambda days: days.pop(100),
            "reversed dates": lambda days: days.reverse(),
            "future date": lambda days: days[-1].update(date="2026-09-19"),
            "negative count": lambda days: days[0].update(count=-1),
            "boolean count": lambda days: days[0].update(count=True),
            "string count": lambda days: days[0].update(count="1"),
            "false zero": lambda days: days[0].update(count=0),
            "false activity": lambda days: days[1].update(count=3),
            "out-of-range level": lambda days: days[0].update(level=5),
            "invalid date": lambda days: days[0].update(date="2026-02-30"),
            "missing calendar": lambda days: days.clear(),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                data = snapshot()
                mutation(data["contributions"]["days"])
                with self.assertRaises(ValueError):
                    profile.validate_snapshot(data, USERNAME)

    def test_stale_calendar_cannot_be_relabelled_as_a_fresh_snapshot(self):
        data = snapshot()
        data["updated_at"] = "2026-09-21T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "stale"):
            profile.validate_snapshot(data, USERNAME)

    def test_wrong_user_incomplete_pagination_duplicate_repos_and_false_stats_fail(self):
        cases = []
        data = snapshot(); data["user"]["login"] = "AnotherUser"; cases.append(data)
        data = snapshot(); data["user"]["public_repos"] = 2; cases.append(data)
        data = snapshot(repo_count=2); data["repos"][1] = deepcopy(data["repos"][0]); cases.append(data)
        data = snapshot(); data["repos"][0]["stargazers_count"] = True; cases.append(data)
        data = snapshot(); data["repos"][0]["html_url"] = "https://evil.example/project"; cases.append(data)
        data = snapshot(); data["updated_at"] = "2026-09-18T12:00:00"; cases.append(data)
        for index, data in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                profile.validate_snapshot(data, USERNAME)


class PublicFetchTests(unittest.TestCase):
    def fake_transport(self, count=101, failing_page=None):
        data = snapshot(end=datetime.now(timezone.utc).date(), repo_count=count)
        requested = []

        def respond(request, timeout):
            requested.append(request)
            parsed = urlsplit(request.full_url)
            if parsed.path.endswith("/repos"):
                page = int(parse_qs(parsed.query)["page"][0])
                self.assertEqual(parse_qs(parsed.query)["per_page"], ["100"])
                if page == failing_page:
                    raise HTTPError(request.full_url, 403, "API rate limit exceeded", {}, None)
                result = [{**repo, "private": False, "owner": {"login": USERNAME}}
                          for repo in data["repos"][(page - 1) * 100:page * 100]]
            elif parsed.path.endswith("/events/public"):
                result = [{**event, "public": True, "repo": {"name": event["repo"]}}
                          for event in data["events"]]
            elif parsed.path.endswith("/contributions"):
                return io.BytesIO(calendar_html(data["contributions"]["days"]).encode())
            else:
                result = data["user"]
            return io.BytesIO(json.dumps(result).encode())

        return data, requested, respond

    def test_real_fetch_walks_rest_pages_and_does_not_send_token_to_html_host(self):
        expected, requests, respond = self.fake_transport()
        with patch.object(profile, "urlopen", side_effect=respond), patch.dict(profile.os.environ, {"GITHUB_TOKEN": "test-token"}):
            actual = profile.fetch_snapshot(USERNAME)
        self.assertEqual(actual["repos"], expected["repos"])
        self.assertEqual(actual["contributions"]["days"], expected["contributions"]["days"])
        self.assertEqual(len([request for request in requests if "/repos?" in request.full_url]), 2)
        for request in requests:
            if urlsplit(request.full_url).hostname == "api.github.com":
                self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
            else:
                self.assertIsNone(request.get_header("Authorization"))

    def test_exact_page_boundary_requests_empty_final_page(self):
        _, requests, respond = self.fake_transport(count=100)
        with patch.object(profile, "urlopen", side_effect=respond):
            self.assertEqual(len(profile.fetch_snapshot(USERNAME)["repos"]), 100)
        self.assertEqual(len([request for request in requests if "/repos?" in request.full_url]), 2)

    def test_mid_fetch_api_failure_preserves_previous_generated_files(self):
        _, _, respond = self.fake_transport(failing_page=2)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            previous = {"README.md": b"Previous README", "profile-content/snapshot.json": b"Previous snapshot",
                        "assets/dashboard.svg": b"Previous artwork"}
            for name, content in previous.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            with patch.object(profile, "ROOT", root), patch.object(profile, "load_config", return_value=config()), \
                 patch.object(profile, "urlopen", side_effect=respond), patch.object(sys, "argv", ["generate_profile.py", "--refresh"]), \
                 patch("sys.stderr", new_callable=io.StringIO) as stderr:
                self.assertEqual(profile.main(), 1)
            self.assertIn("HTTP 403", stderr.getvalue())
            self.assertEqual({str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}, previous)

    def test_transient_api_failure_retries_then_decodes_json(self):
        error = HTTPError("https://api.github.com/test", 503, "Unavailable", {}, None)
        with patch.object(profile, "urlopen", side_effect=[error, io.BytesIO(b'{"ok":true}')]) as transport, \
             patch.object(profile.time, "sleep") as sleep:
            self.assertEqual(profile.request("https://api.github.com/test"), {"ok": True})
        self.assertEqual(transport.call_count, 2)
        sleep.assert_called_once_with(1)


class RenderingTests(unittest.TestCase):
    def test_missing_featured_project_is_skipped_when_another_is_public(self):
        settings, data = config(), snapshot()
        settings["projects"].insert(0, {**settings["projects"][0], "repo": "renamed-or-private"})
        rendered = profile.project_table(settings, data)
        self.assertNotIn("renamed-or-private", rendered)
        self.assertIn("Example", rendered)

    def test_all_missing_featured_projects_fail_clearly(self):
        settings, data = config(), snapshot()
        settings["projects"][0]["repo"] = "renamed-or-private"
        with self.assertRaisesRegex(ValueError, "None of the configured featured projects"):
            profile.project_table(settings, data)

    def test_project_text_and_language_are_html_escaped(self):
        settings, data = config(), snapshot()
        unsafe = '<script>alert("x")</script> & "quoted"'
        for key in ("name", "category", "description", "stack"):
            settings["projects"][0][key] = unsafe
        data["repos"][0]["language"] = unsafe
        rendered = profile.render_readme(settings, data, "{{PROJECTS}}\n{{RECENT_REPOS}}")
        self.assertNotIn("<script>", rendered)
        self.assertEqual(rendered.count(escape(unsafe)), 5)

    def test_unknown_template_variable_fails(self):
        with self.assertRaisesRegex(ValueError, "Unresolved"):
            profile.render_readme(config(), snapshot(), "{{MISSING_VARIABLE}}")

    def test_contribution_city_titles_retain_every_exact_count(self):
        data = snapshot()
        data["contributions"]["days"][0]["count"] = 1234
        image = ET.fromstring(visuals.render_contributions(data))
        titles = [element.text for element in image.iter(validator.SVG + "title")][1:]
        expected = {f'{day["date"]}: {day["count"]:,} contribution' + ("s" if day["count"] != 1 else "")
                    for day in data["contributions"]["days"]}
        self.assertEqual(len(titles), len(expected))
        self.assertEqual(set(titles), expected)

    def test_dashboard_excludes_forks_from_stars_and_repository_total(self):
        data = snapshot(repo_count=2)
        data["repos"][0]["stargazers_count"] = 3
        data["repos"][1].update(fork=True, stargazers_count=1000, language="ForkOnly")
        image = ET.fromstring(visuals.render_dashboard(data))
        description = image.find(validator.SVG + "desc").text
        self.assertIn("1 public non-fork repositories, 3 stars", description)
        self.assertNotIn("ForkOnly", "".join(image.itertext()))


class AssetValidatorTests(unittest.TestCase):
    def test_embedded_png_sprites_are_local_but_embedded_svg_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "pacman.svg"
            png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jz8kAAAAASUVORK5CYII="
            path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,{png}"/></svg>')
            self.assertEqual(validator.validate_svg(path), [])
            for data in ("data:image/svg+xml;base64,PHN2Zy8+", "data:image/png;base64,bm90IGEgcG5n"):
                path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><image href="{data}"/></svg>')
                self.assertTrue(validator.validate_svg(path))

    def test_html_markdown_srcset_and_reference_links_are_all_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "present.svg").write_text("present")
            (root / "README.md").write_text(
                '<img src="./present.svg" alt="Present" />'
                '<source srcset="./present.svg 1x, ./missing-dark.svg 2x">'
                '[Documentation](./missing.md#setup)\n'
                '[Guide][guide]\n[guide]: <./missing guide.md>\n'
                '<a href="https://example.com">Remote</a> [Section](#section)')
            errors = validator.validate_readme(root)
            self.assertEqual(len(errors), 3)
            for name in ("missing-dark.svg", "missing.md", "missing guide.md"):
                self.assertTrue(any(name in error for error in errors))

    def test_missing_alt_text_and_unresolved_variables_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text('<img src="https://example.com/a.svg"> {{UNFILLED}}')
            self.assertEqual(len(validator.validate_readme(root)), 2)

    def test_svg_blocks_active_content_and_remote_resources_but_allows_animation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "test.svg"
            safe = ('<svg xmlns="http://www.w3.org/2000/svg">'
                    '<style>@keyframes move{to{transform:translateX(2px)}}.c{animation:move 2s infinite;fill:var(--c0)}</style>'
                    '<defs><linearGradient id="a"/></defs><path fill="url(#a)"/></svg>')
            path.write_text(safe)
            self.assertEqual(validator.validate_svg(path), [])
            for fragment in ('<script>alert(1)</script>', '<foreignObject/>', '<path onload="run()"/>',
                             '<image href="https://example.com/a.png"/>', '<style>@import "remote.css";</style>',
                             '<path style="fill:url(https://example.com/a.svg)"/>',
                             '<animate attributeName="href" to="https://example.com/a.svg"/>'):
                with self.subTest(fragment=fragment):
                    path.write_text(safe.replace("</svg>", fragment + "</svg>"))
                    self.assertTrue(validator.validate_svg(path))
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><broken></svg>')
            self.assertTrue(validator.validate_svg(path))

    def test_main_visual_requires_associated_title_and_description(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "hero.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">'
                            '<title id="title">Artwork</title><desc id="desc">Descriptive text</desc></svg>')
            self.assertEqual(validator.validate_svg(path, accessible=True), [])
            path.write_text(path.read_text().replace('aria-labelledby="title desc"', 'aria-labelledby="title"'))
            self.assertTrue(validator.validate_svg(path, accessible=True))


if __name__ == "__main__":
    unittest.main()
