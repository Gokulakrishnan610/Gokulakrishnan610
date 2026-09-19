# Profile automation

The profile is generated from editable content and a saved snapshot of public GitHub data. The animated hero, footer, achievement cabinet, statistics, 3D graph, Pac-Man, and snake are committed to this repository. Skill logos, technology badges, and the small trophy GIF use the external image services linked in the README.

## Edit the profile

Change `profile-content/profile.json` for account data, portfolio/contact links, achievements, and featured projects. Change `profile-content/README.template.md` for the intro, skills, achievements, and other copy. The achievement cabinet, statistics, and 3D layouts live in `scripts/visuals.py`; the hero and footer artwork live in `scripts/branding.py`.

Do not edit the generated `README.md`, `profile-content/snapshot.json`, or generated SVGs by hand: the next successful refresh replaces them. The refresh writes `assets/hero.svg`, `assets/footer.svg`, `assets/achievements.svg`, `assets/dashboard.svg`, `assets/contributions.svg`, `assets/pacman.svg`, `assets/pacman-dark.svg`, `assets/snake.svg`, and `assets/snake-light.svg`.

Use Python 3.12 or newer and Node.js 22. The Python generator and validation tools use the standard library. Pac-Man uses the upstream library pinned to a full GitHub commit, with dependency integrity recorded in `package-lock.json`.

```sh
# Render from the checked-in snapshot without making network requests.
python3 scripts/generate_profile.py

# Generate Pac-Man from that same snapshot, without API credentials.
npm ci --ignore-scripts --no-audit --no-fund
npm run generate:pacman

# Test the generator, validate local content, and check reproducibility.
python3 -m unittest discover -s tests -v
python3 scripts/validate_profile.py
python3 scripts/generate_profile.py --check
npm run generate:pacman -- --check

# Fetch current public data, then update the snapshot, README, and artwork.
python3 scripts/generate_profile.py --refresh
npm run generate:pacman
```

Commit the edited source and regenerated outputs together. A local refresh can use an existing `GITHUB_TOKEN` environment variable for GitHub API requests, but no personal access token is required by the hosted workflow. Never store a token in profile content or commit one.

The snake is generated separately by the pinned [Platane/snk action](https://github.com/Platane/snk) during a hosted refresh. The checked-in snake files remain available when running the Python generator locally.

Pac-Man runs locally through `scripts/generate_pacman.mjs`, which adapts the validated snapshot to the library's data-provider format. Rendering makes no network requests and submits no leaderboard scores. Both themes use the same dates/counts; seeded randomness and the snapshot timestamp make them reproducible. Its small ghost sprites are embedded PNGs inside the SVG.

## Refresh workflow

[Refresh profile](../.github/workflows/profile-refresh.yml) runs at minute 17 every six hours, on relevant source pushes to `main`, or through **Actions → Refresh profile → Run workflow**. Select `main` for a manual refresh. A single concurrency group serializes writers.

The workflow tests the generator, fetches public data, generates both Pac-Man and snake themes, and validates all outputs before committing. It stages only the generated README, data snapshot, and nine named SVG files. It uses GitHub's automatically provided `GITHUB_TOKEN` with repository-content write permission; no extra secret or output branch is needed. Action versions are pinned to full commit hashes.

If fetching, generation, or validation fails, no commit is published and the last committed profile stays visible. If someone updates `main` during generation, a conflicting push is rejected safely. Rerun the workflow to regenerate from the new source; the workflow never force-pushes.

If repository rules prevent the bot from pushing, the run fails at publication. Review the run's error and the repository's branch rules; do not grant broader personal-token permissions as a shortcut.

The previous standalone snake workflow has been replaced by this single writer. Any existing `output` branch is historical and is no longer updated or used by the profile.

## What the numbers mean

The snapshot combines the public user API, paginated public repositories, public activity events, and the contribution calendar displayed by GitHub. Values describe visible GitHub activity, not production traffic, deployment uptime, or a measure of skill. Language distributions summarize public repository data rather than time spent coding. Repository push timestamps and public events describe observed activity rather than a promise that a project is currently in development.

The contribution visualization uses the counts GitHub displays for each date. Depending on profile privacy settings, that public calendar can include anonymized private contributions; the workflow does not access private repository content. Public events cover GitHub's available recent event window and can arrive after the underlying activity.

The timestamp on the profile identifies the latest successful data snapshot. This is an automatically refreshed profile, not a realtime connection. GitHub caches images, so a newly committed image may take time to appear. [GitHub's image caching documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls)

GitHub schedules can be delayed or dropped under load and run only from the default branch. In public repositories, scheduled workflows can be disabled after 60 days without repository activity. Use a manual refresh to check a problem, and re-enable a disabled workflow in Actions. [GitHub schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Validation

[Validate profile](../.github/workflows/validate.yml) runs on pull requests, pushes to `main`, and manual requests. It uses read-only repository permissions. Installation downloads the pinned dependency; the checks themselves need no API credentials or live data. It runs unit tests, validates the saved assets and README, and verifies that rendering the saved snapshot reproduces the committed outputs, including both Pac-Man themes.

All visual motion is contained in standalone SVG image assets. GitHub sanitizes README HTML and does not run custom scripts or WebGL inside it. The contribution landscape is an isometric image, so its information remains readable without interactive 3D support. [GitHub's Markdown rendering pipeline](https://github.com/github/markup)

## Credits

The content → generator → committed-assets workflow was inspired by [SivaSabariGanesan's profile repository](https://github.com/SivaSabariGanesan/SivaSabariGanesan). The contribution games use [abozanona's Pac-Man renderer](https://github.com/abozanona/pacman-contribution-graph) and [Platane/snk](https://github.com/Platane/snk). Skill logos come from [Skill Icons](https://skillicons.dev) and badges from [Shields.io](https://shields.io).
