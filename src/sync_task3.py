#!/usr/bin/env python3
"""Fetch Task 3 snapshots, update website data, optionally publish to GitHub Pages."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

DATA_PATHS = ('data/task3-leaderboard.json', 'site/data/leaderboard.json')
EXPECTED_REMOTE = 'Doyona/SJTU-GC-ECE2810J-26FA'


def run(command, root, *, capture=False):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    # GUI launch agents must not depend on a closed editor's askpass socket.
    for key in list(env):
        if key in ('GIT_ASKPASS', 'SSH_ASKPASS') or key.startswith('VSCODE_GIT_'):
            env.pop(key, None)
    env.setdefault('GIT_SSH_COMMAND', 'ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=20')
    result = subprocess.run(command, cwd=root, env=env, text=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None, timeout=900)
    if result.returncode:
        # Git diagnostics can contain credential-bearing URLs. Keep them private.
        raise RuntimeError(f'{command[0]} {command[1]} failed (exit {result.returncode})')
    return result.stdout.strip() if capture else ''


def git(root, *args):
    return run(['git', *args], root, capture=True)


def check_checkout(root):
    if git(root, 'branch', '--show-current') != 'main':
        raise RuntimeError('Website must be on main; no automatic branch switching is performed')
    remote = git(root, 'remote', 'get-url', 'origin')
    if not re.fullmatch(r'(?:https://github\.com/|git@github\.com:)' + re.escape(EXPECTED_REMOTE) + r'(?:\.git)?', remote):
        raise RuntimeError('Website origin does not match the configured course GitHub repository')
    staged = git(root, 'diff', '--cached', '--name-only')
    if staged:
        raise RuntimeError('Existing staged changes found; refusing to include them in publication')
    lines = git(root, 'status', '--porcelain=v1', '--untracked-files=all')
    # strip() removes the leading space from the first porcelain line. Parse
    # the filename separately without relying on its status-column whitespace.
    changed = git(root, 'diff', '--name-only').splitlines()
    untracked = git(root, 'ls-files', '--others', '--exclude-standard').splitlines()
    if any(path not in DATA_PATHS for path in changed + untracked):
        raise RuntimeError('Unrelated website edits found; collect only or commit them separately first')
    return bool(lines)


def refresh_checkout(root):
    dirty = check_checkout(root)
    git(root, 'fetch', 'origin', 'main')
    ahead, behind = map(int, git(root, 'rev-list', '--left-right', '--count', 'HEAD...origin/main').split())
    if behind:
        if ahead or dirty:
            raise RuntimeError('Remote changed while local changes are pending; manual reconciliation required')
        git(root, 'merge', '--ff-only', 'origin/main')
    if ahead:
        subjects = git(root, 'log', 'origin/main..HEAD', '--format=%s').splitlines()
        files = git(root, 'diff', '--name-only', 'origin/main...HEAD').splitlines()
        if any(not title.startswith('data: sync Task 3 lengths') for title in subjects) or any(path not in DATA_PATHS for path in files):
            raise RuntimeError('Unpublished unrelated commits found; refusing to push them')


def valid_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def make_snapshot(source):
    if source.get('release_only') is not True:
        raise ValueError('Collector must enforce release-only provenance; preview snapshots are rejected')
    if source.get('read_errors') != 0:
        raise ValueError('Incomplete collection: previous published data will be retained')
    total = source.get('student_repositories')
    students = source.get('students')
    if not valid_integer(total) or total == 0 or not isinstance(students, list):
        raise ValueError('Empty or invalid student inventory')
    latest = {}
    for row in students:
        repo = row.get('repository', '')
        if not repo.startswith('ece281s1/') or not repo.endswith('project'):
            raise ValueError('Unexpected student repository')
        if row.get('status') in ('read_error', 'stale_after_read_error'):
            raise ValueError('Stale student result; keep previous published data')
        if row.get('configuration') not in (None, 'p3-release'):
            raise ValueError('Preview configuration cannot enter the release-only website')
        timestamp = row.get('generated_at') or ''
        if repo not in latest or timestamp > (latest[repo].get('generated_at') or ''):
            latest[repo] = row
    if len(latest) != total:
        raise ValueError('Student inventory count mismatch')
    entries = []
    counts = {'total': total, 'withResults': 0, 'complete': 0, 'failedOrIncomplete': 0, 'noVisibleResult': 0}
    for repo, row in sorted(latest.items()):
        if row['status'] == 'no_release_result':
            counts['noVisibleResult'] += 1
            continue
        counts['withResults'] += 1
        if row['status'] != 'complete_valid':
            counts['failedOrIncomplete'] += 1
            continue
        if (row.get('released') is not True or row.get('configuration') != 'p3-release'
                or row.get('release_event') != 'release' or row.get('release_tag') != 'p3'
                or not re.fullmatch(r'(?:\.gitea/workflows/)?release\.ya?ml@refs/tags/p3', row.get('release_workflow') or '')):
            raise ValueError('Complete result lacks verified P3 release provenance')
        if row.get('verified_cases') != 20 or row.get('task3_cases') != 20:
            raise ValueError('Complete result lacks 20 verified cases')
        rounds, steps = row.get('task3_total_rounds'), row.get('task3_total_movement_steps')
        if not valid_integer(rounds) or not valid_integer(steps):
            raise ValueError('Complete result has missing or invalid length')
        generated = row.get('generated_at')
        # Joint-Teapot uses the course host's China Standard Time without an offset.
        stamp = datetime.strptime(generated, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('Asia/Shanghai')).isoformat()
        name = re.sub(r'\d+project$', '', repo.split('/')[1])
        entries.append({'id': 'p3-' + hashlib.sha256(repo.encode()).hexdigest()[:16],
                        'name': name or repo.split('/')[1], 'submittedAt': stamp,
                        'metrics': {'rounds': rounds, 'movementSteps': steps},
                        'source': {'issue': row.get('issue_url'), 'runId': row.get('run_id'),
                                   'configuration': row.get('configuration'), 'commit': row.get('commit'),
                                   'event': 'release', 'tag': 'p3', 'workflow': row['release_workflow']},
                        'released': True, 'caseSetIdentity': None})
        counts['complete'] += 1
    return {'schemaVersion': 1, 'organization': 'ece281s1', 'caseCount': 20,
            'releaseOnly': True, 'referenceOnly': True, 'coverage': counts, 'entries': entries}


def project_from_snapshot(snapshot):
    return {'id': 'project-03', 'title': 'Project 03 · Task 3',
            'description': '每小时同步正式发布 p3 标签后触发的判题，仅展示 20 个用例全部通过的 release 结果，不收录预览运行。',
            'releaseOnly': True, 'referenceOnly': True, 'timeLabel': 'Release 结果时间',
            'primaryMetric': 'rounds',
            'metrics': [{'key': 'rounds', 'label': '同步轮数', 'unit': '轮', 'direction': 'asc', 'decimals': 0},
                        {'key': 'movementSteps', 'label': '移动步数', 'unit': '步', 'direction': 'asc', 'decimals': 0}],
            'entries': snapshot['entries'], 'coverage': snapshot['coverage']}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        temporary = Path(stream.name)
    temporary.replace(path)


def update_files(root, source):
    snapshot = make_snapshot(source)
    public_path, site_path = [root / name for name in DATA_PATHS]
    site = json.loads(site_path.read_text())
    project = project_from_snapshot(snapshot)
    previous = json.loads(public_path.read_text()) if public_path.exists() else None
    if previous:
        previous.pop('updatedAt', None)
    existing = next((item for item in site['projects'] if item['id'] == 'project-03'), None)
    obsolete = any(item['id'] in ('project-01', 'project-02') for item in site['projects'])
    if previous == snapshot and existing == project and not obsolete:
        return False
    now = datetime.now(timezone.utc).isoformat()
    site['projects'] = [project if item['id'] == 'project-03' else item for item in site['projects']
                        if item['id'] not in ('project-01', 'project-02')]
    if existing is None:
        site['projects'].append(project)
    site['updatedAt'] = now
    snapshot['updatedAt'] = now
    # Validate against the actual website schema before replacing published inputs.
    script = "import {validateData} from './site/leaderboard.mjs'; let s=''; for await(const c of process.stdin)s+=c; validateData(JSON.parse(s));"
    checked = subprocess.run(['node', '--input-type=module', '-e', script], cwd=root,
                             input=json.dumps(site), text=True, capture_output=True, timeout=30)
    if checked.returncode:
        raise ValueError('Website schema rejected the new data')
    atomic_json(public_path, snapshot)
    atomic_json(site_path, site)
    return True


def publish(root):
    # A failed push leaves a data-only commit; refresh_checkout permits its retry.
    run(['npm', 'test'], root)
    run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'test', '-p', 'test_*.py'], root)
    run(['npm', 'run', 'build'], root)
    git(root, 'add', '--', *DATA_PATHS)
    staged = git(root, 'diff', '--cached', '--name-only')
    if staged:
        if any(path not in DATA_PATHS for path in staged.splitlines()):
            raise RuntimeError('Unexpected staged file; publication stopped')
        git(root, 'commit', '-m', 'data: sync Task 3 lengths')
    ahead = int(git(root, 'rev-list', '--count', 'origin/main..HEAD'))
    if ahead:
        git(root, 'push', 'origin', 'HEAD:main')
        print('Published Task 3 data to GitHub; existing Pages workflow will deploy.', flush=True)
    else:
        print('No changed results; no commit or push needed.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--website-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--exporter', type=Path, help='Existing P3 src/export_class_lengths.py')
    parser.add_argument('--env-file', type=Path, help='Existing Joint-Teapot credentials; never copied into website')
    parser.add_argument('--source-json', type=Path, help='Offline verification using a saved class-lengths.json')
    parser.add_argument('--publish', action='store_true', help='Commit and push only the two public JSON data files')
    args = parser.parse_args()
    root = args.website_root.resolve()
    if args.source_json and args.publish:
        parser.error('Offline fixture mode cannot publish')
    lock_dir = root/'data/task3'
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir/'sync.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another Task 3 sync is already running; skipped.')
            return
        if args.publish:
            refresh_checkout(root)
        if args.source_json:
            source_path = args.source_json
        else:
            if not args.exporter or not args.env_file:
                parser.error('--exporter and --env-file are required for live collection')
            run([sys.executable, '-B', str(args.exporter.resolve()), '--organization', 'ece281s1',
                 '--env-file', str(args.env_file.resolve()), '--output-dir', str(root/'data/task3')], root)
            source_path = root/'data/task3/class-lengths.json'
        source = json.loads(source_path.read_text())
        changed = update_files(root, source)
        print(f'Task 3 results {"updated" if changed else "unchanged"}; {source["student_repositories"]} student repositories checked.', flush=True)
        if args.publish:
            publish(root)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f'Task 3 sync failed: {error}', file=sys.stderr)
        raise SystemExit(1)
