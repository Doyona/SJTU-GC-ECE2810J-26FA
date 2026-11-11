import { validateData, rankEntries, visibleEntries, csvCell } from './leaderboard.mjs';

const $ = id => document.getElementById(id);
const state = { data: null, project: null, query: '', sortKey: '', direction: '' };
const dateFormat = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Shanghai' });
const timeFormat = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' });
const submittedAtFormat = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'medium', timeZone: 'Asia/Shanghai' });
const entryColumns = [
  { key: 'submittedAt', label: '提交时间', direction: 'desc' },
  { key: 'name', label: '姓名' }
];
const formatMetric = (value, metric) => value.toLocaleString('en-US', { minimumFractionDigits: metric.decimals, maximumFractionDigits: metric.decimals });
const metricLabel = metric => metric.unit ? `${metric.label} (${metric.unit})` : metric.label;
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function load() {
  $('error-state').hidden = true;
  $('board-status').textContent = 'Loading results';
  $('retry').disabled = true;
  try {
    const response = await fetch(new URL('./data/leaderboard.json', import.meta.url), { cache: 'no-cache' });
    if (!response.ok) throw new Error(`Request failed (${response.status}).`);
    state.data = validateData(await response.json());
    $('demo-banner').hidden = !state.data.demo;
    const requested = new URL(location.href).searchParams.get('project');
    const selected = state.data.projects.find(project => project.id === requested) || state.data.projects[0];
    $('project-tabs').replaceChildren(...state.data.projects.map((project, index) => {
      const button = element('button', 'project-tab');
      button.type = 'button';
      button.dataset.project = project.id;
      button.append(element('span', 'tab-number', String(index + 1).padStart(2, '0')), document.createTextNode(project.title));
      button.addEventListener('click', () => selectProject(project));
      return button;
    }));
    selectProject(selected, false);
    $('export').disabled = false;
  } catch (error) {
    $('error-state').hidden = false;
    $('project-title').textContent = 'Leaderboard unavailable';
    $('project-description').textContent = 'Please try again in a moment.';
    $('error-message').textContent = `Please check the leaderboard data and your connection. ${error.message}`;
    $('board-status').textContent = 'Unavailable';
    $('ranking-note').textContent = 'Results are temporarily unavailable.';
    $('export').disabled = true;
  } finally {
    $('retry').disabled = false;
  }
}

function selectProject(project, updateUrl = true) {
  state.project = project;
  state.sortKey = project.primaryMetric;
  state.direction = project.metrics.find(metric => metric.key === project.primaryMetric).direction;
  for (const button of $('project-tabs').children) button.setAttribute('aria-current', String(button.dataset.project === project.id));
  if (updateUrl) {
    const url = new URL(location.href);
    url.searchParams.set('project', project.id);
    history.replaceState(null, '', url);
  }
  $('project-title').textContent = project.title;
  $('project-description').textContent = project.description;
  $('table-caption').textContent = `${project.title} rankings`;
  const ranked = rankEntries(project);
  const primary = project.metrics.find(metric => metric.key === project.primaryMetric);
  $('board-status').textContent = state.data.demo ? 'Sample results' : ranked.length ? 'Published results' : 'Awaiting results';
  $('ranked-count').textContent = ranked.length;
  $('best-label').textContent = primary.key === 'steps' ? 'FEWEST STEPS' : `BEST ${primary.label.toUpperCase()}`;
  $('best-value').textContent = ranked.length ? formatMetric(ranked[0].metrics[primary.key], primary) : '—';
  $('best-unit').textContent = primary.unit;
  const updated = new Date(state.data.updatedAt);
  $('updated-date').textContent = dateFormat.format(updated);
  $('updated-time').textContent = `${timeFormat.format(updated)} CST (UTC+8)`;
  const direction = primary.direction === 'asc' ? '从小到大' : '从大到小';
  $('ranking-note').textContent = `默认按「${primary.label}」${direction}排列，成绩相同则并列。`;
  $('about-description').textContent = '提交时间以北京时间（UTC+8）显示。';
  renderTable();
}

function renderTable() {
  const project = state.project;
  const head = element('tr');
  const columns = [...entryColumns, ...project.metrics.map(metric => ({ ...metric, label: metricLabel(metric), numeric: true }))];
  for (const column of columns) {
    const th = element('th', column.numeric ? 'numeric' : '');
    th.scope = 'col';
    const selected = column.key === state.sortKey;
    th.setAttribute('aria-sort', selected ? (state.direction === 'asc' ? 'ascending' : 'descending') : 'none');
    const button = element('button', '', column.label);
    button.type = 'button';
    button.dataset.sort = column.key;
    const arrow = element('span', 'sort-indicator', selected ? (state.direction === 'asc' ? '↑' : '↓') : '↕');
    arrow.setAttribute('aria-hidden', 'true');
    button.append(arrow);
    button.addEventListener('click', () => {
      state.direction = selected ? (state.direction === 'asc' ? 'desc' : 'asc') : column.direction || 'asc';
      state.sortKey = column.key;
      renderTable();
      // The header is rebuilt when sort state changes; retain keyboard focus.
      [...$('table-head').querySelectorAll('button')].find(item => item.dataset.sort === column.key)?.focus();
    });
    th.append(button);
    head.append(th);
  }
  $('table-head').replaceChildren(head);
  const entries = visibleEntries(project, state.query, state.sortKey, state.direction);
  $('table-body').replaceChildren(...entries.map(entry => {
    const tr = element('tr', entry.rank === 1 ? 'top-team' : '');
    const submission = element('td');
    if (entry.submittedAt) {
      const time = element('time', '', submittedAtFormat.format(new Date(entry.submittedAt)));
      time.dateTime = entry.submittedAt;
      submission.append(time);
    } else {
      submission.textContent = '—';
    }
    const name = element('td');
    const cell = element('div', 'team-cell');
    const initials = entry.name.trim().split(/\s+/).slice(0, 2).map(word => Array.from(word)[0]).join('').toUpperCase();
    const avatar = element('span', 'avatar', initials);
    avatar.setAttribute('aria-hidden', 'true');
    cell.append(avatar, element('span', 'team-name', entry.name));
    name.append(cell);
    tr.append(submission, name);
    for (const metric of project.metrics) {
      const value = entry.metrics === null ? '—' : formatMetric(entry.metrics[metric.key], metric);
      tr.append(element('td', `numeric${metric.key === project.primaryMetric ? ' metric-primary' : ''}`, value));
    }
    return tr;
  }));
  $('empty-state').hidden = entries.length !== 0;
  $('empty-state').querySelector('h3').textContent = project.entries.length ? 'No matching names' : 'No results yet';
  $('empty-state').querySelector('p').textContent = project.entries.length ? 'Try another name.' : 'Results appear here after publication.';
  $('clear-search').hidden = !state.query;
  $('result-count').textContent = `${entries.length} of ${project.entries.length} entries`;
}

$('search').addEventListener('input', event => {
  state.query = event.target.value;
  if (state.project) renderTable();
});
$('clear-search').addEventListener('click', () => {
  state.query = '';
  $('search').value = '';
  renderTable();
  $('search').focus();
});
$('retry').addEventListener('click', load);
document.addEventListener('keydown', event => {
  if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
    event.preventDefault();
    $('search').focus();
  }
});
$('export').addEventListener('click', () => {
  const project = state.project;
  const headers = [...entryColumns.map(column => column.label), ...project.metrics.map(metricLabel)];
  const rows = visibleEntries(project, state.query, state.sortKey, state.direction).map(entry => [entry.submittedAt ?? '', entry.name, ...project.metrics.map(metric => entry.metrics?.[metric.key] ?? '')]);
  const csv = '\uFEFF' + [headers, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
  const link = element('a');
  link.href = url;
  link.download = `${project.id}-leaderboard.csv`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

load();
