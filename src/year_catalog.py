"""Year catalog storage and validation; no network or Git writes."""
import copy
from datetime import datetime, timezone
import json
import subprocess

DEFAULT_YEAR = '2026-fall'
DEFAULT_ORGANIZATION = 'ece281s1'


def catalog(data):
    if 'years' in data:
        return data
    return {'schemaVersion': 2, 'activeYear': DEFAULT_YEAR, 'years': [dict(
        data, id=DEFAULT_YEAR, year=2026, term='fall', label='Fall 2026',
        organization=DEFAULT_ORGANIZATION, archived=False)]}


def find_year(data, year_id):
    for year in data['years']:
        if year['id'] == year_id:
            return year
    raise ValueError(f'Unknown year: {year_id}')


def validate(root, data):
    script = "import {validateData} from './site/leaderboard.mjs'; let s=''; for await(const c of process.stdin)s+=c; validateData(JSON.parse(s));"
    checked = subprocess.run(['node', '--input-type=module', '-e', script], cwd=root,
                             input=json.dumps(data), text=True, capture_output=True, timeout=30)
    if checked.returncode:
        raise ValueError('Website schema rejected the year catalog')


def add_year(data, year, term, organization):
    year_id = f'{year}-{term}'
    if any(item['id'] == year_id for item in data['years']):
        raise ValueError(f'Year already exists: {year_id}')
    template = copy.deepcopy(find_year(data, data['activeYear']))
    template.update(id=year_id, year=year, term=term, label=f'{term.title()} {year}',
                    organization=organization, archived=False, demo=False,
                    updatedAt=datetime.now(timezone.utc).isoformat())
    for project in template['projects']:
        project['entries'] = []
        project.pop('coverage', None)
    data['years'].append(template)
    return year_id


def set_default(data, year_id):
    if find_year(data, year_id)['archived']:
        raise ValueError('Unarchive the year before making it the default')
    data['activeYear'] = year_id


def archive_year(data, year_id, archived=True):
    year = find_year(data, year_id)
    if archived and data['activeYear'] == year_id:
        raise ValueError('Choose another default year before archiving this year')
    year['archived'] = archived


def remove_empty_year(data, year_id):
    year = find_year(data, year_id)
    if data['activeYear'] == year_id:
        raise ValueError('The default year cannot be removed')
    if any(project['entries'] for project in year['projects']):
        raise ValueError('A year with results can only be archived')
    data['years'].remove(year)
