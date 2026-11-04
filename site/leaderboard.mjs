export function validateData(data) {
  const fail = (message) => { throw new Error(`Invalid leaderboard data: ${message}`); };
  const isText = value => typeof value === 'string' && value.trim().length > 0;
  const isDate = value => isText(value) && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value));
  if (!data || typeof data !== 'object') fail('expected an object');
  if (typeof data.demo !== 'boolean') fail('demo must be true or false');
  if (!isDate(data.updatedAt)) fail('updatedAt must be an ISO timestamp with a timezone');
  if (!Array.isArray(data.projects) || !data.projects.length) fail('at least one project is required');
  const ids = new Set();
  for (const project of data.projects) {
    if (!project || !isText(project.id) || !/^[a-z0-9-]+$/.test(project.id) || ids.has(project.id)) fail('project IDs must be unique URL-safe strings');
    ids.add(project.id);
    if (!isText(project.title) || !isText(project.description)) fail(`${project.id}: title and description are required`);
    if (!Array.isArray(project.metrics) || !project.metrics.length) fail(`${project.id}: metrics are required`);
    const metrics = new Set();
    for (const metric of project.metrics) {
      if (!metric || !isText(metric.key) || metrics.has(metric.key)) fail(`${project.id}: metric keys must be unique`);
      metrics.add(metric.key);
      if (!isText(metric.label) || typeof metric.unit !== 'string') fail(`${project.id}: metric labels and units are required`);
      if (!['asc', 'desc'].includes(metric.direction)) fail(`${project.id}: metric direction must be asc or desc`);
      if (!Number.isInteger(metric.decimals) || metric.decimals < 0 || metric.decimals > 6) fail(`${project.id}: decimals must be an integer from 0 to 6`);
    }
    if (!metrics.has(project.primaryMetric)) fail(`${project.id}: primaryMetric must match a metric key`);
    if (!Array.isArray(project.entries)) fail(`${project.id}: entries must be an array`);
    const teams = new Set();
    for (const entry of project.entries) {
      if (!entry || !isText(entry.id) || teams.has(entry.id)) fail(`${project.id}: team IDs must be unique`);
      teams.add(entry.id);
      if (!isText(entry.name) || !Array.isArray(entry.members) || !entry.members.every(isText)) fail(`${project.id}: team name and members are required`);
      if (!isText(entry.language) || !isDate(entry.updatedAt)) fail(`${project.id}: language and ISO updatedAt are required`);
      if (!entry.metrics || typeof entry.metrics !== 'object') fail(`${project.id}: team metrics are required`);
      for (const metric of project.metrics) {
        if (typeof entry.metrics[metric.key] !== 'number' || !Number.isFinite(entry.metrics[metric.key]) || entry.metrics[metric.key] < 0) fail(`${project.id}/${entry.id}: ${metric.key} must be a nonnegative finite number`);
      }
    }
  }
  return data;
}

export function rankEntries(project) {
  const metric = project.metrics.find(item => item.key === project.primaryMetric);
  const entries = [...project.entries].sort((a, b) => compareMetric(a, b, metric.key, metric.direction));
  let rank = 0;
  return entries.map((entry, index) => {
    if (index === 0 || entry.metrics[metric.key] !== entries[index - 1].metrics[metric.key]) rank = index + 1;
    return { ...entry, rank };
  });
}

function compareMetric(a, b, key, direction) {
  const difference = a.metrics[key] - b.metrics[key];
  return (direction === 'asc' ? difference : -difference) || a.id.localeCompare(b.id, 'en');
}

export function visibleEntries(project, query = '', sortKey = project.primaryMetric, direction) {
  const metric = project.metrics.find(item => item.key === sortKey);
  const normalized = query.trim().toLocaleLowerCase();
  const entries = rankEntries(project).filter(entry => `${entry.name} ${entry.members.join(' ')}`.toLocaleLowerCase().includes(normalized));
  if (metric) entries.sort((a, b) => compareMetric(a, b, sortKey, direction || metric.direction));
  else if (sortKey === 'name') entries.sort((a, b) => (direction === 'desc' ? -1 : 1) * a.name.localeCompare(b.name, 'en') || a.id.localeCompare(b.id, 'en'));
  else if (sortKey === 'rank') entries.sort((a, b) => (direction === 'desc' ? -1 : 1) * (a.rank - b.rank) || a.id.localeCompare(b.id, 'en'));
  return entries;
}

export function csvCell(value) {
  let text = String(value);
  // Keep names supplied through the data file from becoming spreadsheet formulas.
  if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}
