// Render the pinned Pac-Man library from our validated GitHub snapshot, offline.
// A fetch adapter supplies the snapshot in the upstream provider's expected shape.
import { readFile, writeFile, rename } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
process.env.TZ = 'UTC';
const check = process.argv.includes('--check');
execFileSync(process.env.PYTHON || 'python3', [path.join(root, 'scripts/generate_profile.py'), '--check'], { stdio: 'inherit' });
const snapshot = JSON.parse(await readFile(path.join(root, 'profile-content/snapshot.json'), 'utf8'));
const levels = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'];
const days = snapshot.contributions.days.map(day => ({
  date: day.date, contributionCount: day.count,
  contributionLevel: levels[day.level], color: ''
}));
const actualFetch = globalThis.fetch;
const ActualDate = globalThis.Date;
const actualRandom = Math.random;
const epoch = ActualDate.parse(snapshot.updated_at);
let requests = 0;
// This process never contacts GitHub or any leaderboard service.
globalThis.fetch = async (url, options) => {
  assert.equal(url, 'https://api.github.com/graphql', 'Unexpected network request');
  assert.equal(JSON.parse(options.body).variables.login, snapshot.user.login);
  requests++;
  return new Response(JSON.stringify({data: {user: {contributionsCollection: {
    contributionCalendar: {weeks: [{contributionDays: days}]}
  }}}}), {status: 200, headers: {'Content-Type': 'application/json'}});
};
globalThis.Date = class extends ActualDate {
  constructor(...args) { super(...(args.length ? args : [epoch])); }
  static now() { return epoch; }
};
const outputs = [];
try {
  const { PacmanRenderer } = await import('pacman-contribution-graph');
  for (const [theme, filename] of [['github', 'pacman.svg'], ['github-dark', 'pacman-dark.svg']]) {
    let seed = createHash('sha256').update(JSON.stringify(days)).digest().readUInt32BE(0) || 1;
    Math.random = () => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    let svg;
    const renderer = new PacmanRenderer({
      platform: 'github', username: snapshot.user.login, gameTheme: theme,
      githubSettings: {accessToken: 'offline-snapshot-adapter'},
      svgCallback: value => { svg = value; }
    });
    const result = await renderer.start();
    assert.equal(result.contributions.length, days.length);
    assert.equal(result.contributions.reduce((sum, day) => sum + day.count, 0), days.reduce((sum, day) => sum + day.contributionCount, 0));
    assert.ok(svg?.includes('<animate'), 'Renderer did not produce an animated SVG');
    // Upstream omits a viewBox; add it so the game scales inside GitHub's README.
    svg = svg.replace(/<svg width="(\d+)" height="(\d+)"/, '<svg viewBox="0 0 $1 $2" role="img" aria-label="Pac-Man contribution animation" width="$1" height="$2"');
    outputs.push([path.join(root, 'assets', filename), svg.replace(/[ \t]+$/gm, '').trimEnd() + '\n']);
  }
  assert.equal(requests, 2, 'Expected exactly one local data request per theme');
} finally {
  globalThis.fetch = actualFetch;
  globalThis.Date = ActualDate;
  Math.random = actualRandom;
}
for (const [destination, svg] of outputs) {
  if (check) {
    assert.equal(await readFile(destination, 'utf8'), svg, `Stale Pac-Man asset: ${destination}`);
  } else {
    await writeFile(destination + '.tmp', svg);
    await rename(destination + '.tmp', destination);
  }
}
console.log(check ? 'Pac-Man assets match the saved snapshot.' : 'Rendered both Pac-Man themes from the saved contribution calendar.');
