import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateData, rankEntries, visibleEntries, csvCell } from '../site/leaderboard.mjs';

const data = JSON.parse(await readFile(new URL('../site/data/leaderboard.json', import.meta.url), 'utf8'));

test('published dataset satisfies the schema', () => {
  assert.equal(validateData(data), data);
});

test('score rankings use descending competition ranks including ties', () => {
  assert.deepEqual(rankEntries(data.projects[0]).map(entry => entry.rank), [1, 2, 3, 3, 5, 6, 7, 8]);
  assert.equal(rankEntries(data.projects[0])[0].id, 'team-01');
});

test('runtime rankings put the lowest measurement first without mutating source data', () => {
  const project = structuredClone(data.projects[1]);
  const original = structuredClone(project);
  assert.equal(rankEntries(project)[0].id, 'team-02');
  assert.deepEqual(project, original);
});

test('search matches members and names case insensitively while retaining global rank', () => {
  assert.deepEqual(visibleEntries(data.projects[0], '  MEMBER I ').map(entry => entry.rank), [5]);
  assert.equal(visibleEntries(data.projects[0], 'next COMMIT')[0].rank, 8);
  assert.deepEqual(visibleEntries(data.projects[0], 'not a team'), []);
});

test('sorting by another metric retains original ranks and supports both directions', () => {
  const project = data.projects[0];
  assert.equal(visibleEntries(project, '', 'memory', 'asc')[0].rank, 3);
  assert.equal(visibleEntries(project, '', 'memory', 'desc')[0].rank, 8);
});

test('empty boards are valid and rank without errors', () => {
  const empty = structuredClone(data);
  empty.projects[0].entries = [];
  assert.doesNotThrow(() => validateData(empty));
  assert.deepEqual(rankEntries(empty.projects[0]), []);
});

test('invalid measurements, IDs, dates, and sort rules are rejected before publishing', () => {
  const mutations = [
    copy => { copy.projects[0].entries[0].metrics.score = '98'; },
    copy => { copy.projects[0].entries[0].metrics.score = -1; },
    copy => { copy.projects[0].entries[0].metrics.score = NaN; },
    copy => { delete copy.projects[0].entries[0].metrics.runtime; },
    copy => { copy.projects[0].entries[1].id = 'team-01'; },
    copy => { copy.projects[1].id = 'project-01'; },
    copy => { copy.projects[0].primaryMetric = 'missing'; },
    copy => { copy.projects[0].metrics[0].direction = 'up'; },
    copy => { copy.updatedAt = '2026-11-04'; }
  ];
  for (const mutate of mutations) {
    const copy = structuredClone(data);
    mutate(copy);
    assert.throws(() => validateData(copy), /Invalid leaderboard data/);
  }
});

test('CSV escaping handles quotes, commas, newlines, and spreadsheet formulas', () => {
  assert.equal(csvCell('Team "A", B\nC'), '"Team ""A"", B\nC"');
  assert.equal(csvCell('=SUM(A1:A2)'), '"\'=SUM(A1:A2)"');
  assert.equal(csvCell(98.75), '"98.75"');
});
