import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateData, rankEntries, visibleEntries, csvCell } from '../site/leaderboard.mjs';

const published = JSON.parse(await readFile(new URL('../site/data/leaderboard.json', import.meta.url), 'utf8'));
const updatedAt = '2026-11-04T13:00:00Z';
const scoreProject = {
  id: 'score-project',
  title: 'Score project',
  description: 'Ranked by score.',
  primaryMetric: 'score',
  metrics: [
    { key: 'score', label: 'Score', unit: 'pts', direction: 'desc', decimals: 2 },
    { key: 'runtime', label: 'Runtime', unit: 'ms', direction: 'asc', decimals: 1 },
    { key: 'memory', label: 'Memory', unit: 'MB', direction: 'asc', decimals: 1 }
  ],
  entries: [
    { id: 'team-03', name: 'Team Three', members: ['Member C'], language: 'C++', metrics: { score: 70, runtime: 5, memory: 1 }, updatedAt },
    { id: 'team-01', name: 'Team One', members: ['Member A'], language: 'C++', metrics: { score: 90, runtime: 3, memory: 4 }, updatedAt },
    { id: 'team-02', name: 'Team Two', members: ['Member B'], language: 'C++', metrics: { score: 80, runtime: 2, memory: 3 }, updatedAt },
    { id: 'team-04', name: 'Team Four', members: ['Member D'], language: 'C++', metrics: { score: 70, runtime: 6, memory: 2 }, updatedAt },
    { id: 'team-05', name: 'Team Five', members: ['Member E'], language: 'C++', metrics: { score: 60, runtime: 7, memory: 5 }, updatedAt }
  ]
};
const runtimeProject = { ...scoreProject, id: 'runtime-project', title: 'Runtime project', description: 'Ranked by runtime.', primaryMetric: 'runtime' };
const data = { demo: true, updatedAt, projects: [scoreProject, runtimeProject] };

test('published dataset satisfies the schema', () => {
  assert.equal(validateData(published), published);
});

test('search results can rank the same entries independently by steps or time', () => {
  const project = {
    ...published.projects[0],
    entries: [
      { id: 'entry-a', name: '张三', metrics: { searchTime: 3.125, steps: 9 } },
      { id: 'entry-b', name: '李四', metrics: { searchTime: 4.75, steps: 7 } },
      { id: 'entry-c', name: '王五', metrics: { searchTime: 2.5, steps: 7 } }
    ]
  };
  const scores = { ...published, projects: [project] };
  assert.doesNotThrow(() => validateData(scores));
  assert.deepEqual(rankEntries(project).map(({ name, rank }) => [name, rank]), [['李四', 1], ['王五', 1], ['张三', 3]]);
  const timeBoard = { ...project, primaryMetric: 'searchTime' };
  assert.deepEqual(rankEntries(timeBoard).map(({ name, rank }) => [name, rank]), [['王五', 1], ['张三', 2], ['李四', 3]]);
  assert.deepEqual(visibleEntries(project, '', 'searchTime').map(entry => entry.name), ['王五', '张三', '李四']);
  assert.equal(visibleEntries(project, '张三')[0].rank, 3);

  project.entries[0].metrics.steps = 8.5;
  assert.throws(() => validateData(scores), /steps must be a nonnegative whole number/);
});

test('score rankings use descending competition ranks including ties', () => {
  assert.deepEqual(rankEntries(scoreProject).map(entry => entry.rank), [1, 2, 3, 3, 5]);
  assert.equal(rankEntries(scoreProject)[0].id, 'team-01');
});

test('runtime rankings put the lowest measurement first without mutating source data', () => {
  const project = structuredClone(runtimeProject);
  const original = structuredClone(project);
  assert.equal(rankEntries(project)[0].id, 'team-02');
  assert.deepEqual(project, original);
});

test('search matches members and names case insensitively while retaining global rank', () => {
  assert.deepEqual(visibleEntries(scoreProject, '  MEMBER E ').map(entry => entry.rank), [5]);
  assert.equal(visibleEntries(scoreProject, 'team TWO')[0].rank, 2);
  assert.deepEqual(visibleEntries(scoreProject, 'not a team'), []);
});

test('sorting by another metric retains original ranks and supports both directions', () => {
  assert.equal(visibleEntries(scoreProject, '', 'memory', 'asc')[0].rank, 3);
  assert.equal(visibleEntries(scoreProject, '', 'memory', 'desc')[0].rank, 5);
});

test('submission times sort chronologically across timezones and leave undated entries last', () => {
  const project = {
    ...published.projects[0],
    entries: [
      { id: 'entry-a', name: '张三', submittedAt: '2026-11-11T15:00:00+08:00', metrics: { searchTime: 3, steps: 5 } },
      { id: 'entry-b', name: '李四', submittedAt: '2026-11-11T08:00:00Z', metrics: { searchTime: 4, steps: 9 } },
      { id: 'entry-c', name: '王五', metrics: { searchTime: 2, steps: 4 } },
      { id: 'baseline', name: 'Baseline', metrics: null }
    ]
  };
  const scores = { ...published, projects: [project] };
  assert.doesNotThrow(() => validateData(scores));
  assert.deepEqual(visibleEntries(project, '', 'submittedAt').map(entry => entry.id), ['entry-b', 'entry-a', 'entry-c', 'baseline']);
  assert.deepEqual(visibleEntries(project, '', 'submittedAt', 'asc').map(entry => entry.id), ['entry-a', 'entry-b', 'entry-c', 'baseline']);

  project.entries[0].submittedAt = '2026-11-11T15:00:00';
  assert.throws(() => validateData(scores), /submittedAt must be an ISO timestamp with a timezone/);
});

test('empty boards are valid and rank without errors', () => {
  const empty = structuredClone(data);
  empty.projects[0].entries = [];
  assert.doesNotThrow(() => validateData(empty));
  assert.deepEqual(rankEntries(empty.projects[0]), []);
});

test('an unmeasured baseline appears in results without receiving a rank', () => {
  const baseline = { id: 'baseline', name: 'Baseline', members: [], language: '—', metrics: null, updatedAt };
  const project = { ...scoreProject, entries: [baseline] };
  assert.doesNotThrow(() => validateData({ ...data, projects: [project] }));
  assert.deepEqual(rankEntries(project), []);
  assert.deepEqual(visibleEntries(project, 'BASELINE', 'memory', 'desc'), [{ ...baseline, rank: null }]);
  assert.deepEqual(visibleEntries(project, 'Team One'), []);

  project.entries.push(scoreProject.entries[0]);
  assert.deepEqual(visibleEntries(project, '', 'memory', 'desc').map(entry => entry.rank), [1, null]);
});

test('invalid measurements, IDs, dates, and sort rules are rejected before publishing', () => {
  const mutations = [
    copy => { copy.projects[0].entries[0].metrics.score = '98'; },
    copy => { copy.projects[0].entries[0].metrics.score = -1; },
    copy => { copy.projects[0].entries[0].metrics.score = NaN; },
    copy => { copy.projects[0].entries[0].metrics = null; },
    copy => { delete copy.projects[0].entries[0].metrics.runtime; },
    copy => { copy.projects[0].entries[1].id = copy.projects[0].entries[0].id; },
    copy => { copy.projects[1].id = copy.projects[0].id; },
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
