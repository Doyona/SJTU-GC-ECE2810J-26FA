#!/usr/bin/env python3
"""Manage durable leaderboard periods. Never commits or pushes."""
import argparse
import fcntl
import json
from pathlib import Path
import sys

from sync_task3 import atomic_json
from year_catalog import add_year, archive_year, catalog, remove_empty_year, set_default, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--website-root', type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    add = commands.add_parser('add')
    add.add_argument('--year', type=int, required=True, choices=range(2000, 2200), metavar='YEAR')
    add.add_argument('--term', choices=['spring', 'summer', 'fall', 'winter'], required=True)
    add.add_argument('--organization', required=True)
    for name in ['set-default', 'archive', 'unarchive', 'remove-empty']:
        commands.add_parser(name).add_argument('year_id')
    args = parser.parse_args()
    root = args.website_root.resolve()
    lock_path = root/'data/task3/sync.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = root/'site/data/leaderboard.json'
        data = catalog(json.loads(path.read_text()))
        validate(root, data)
        if args.command == 'list':
            for year in sorted(data['years'], key=lambda item: item['id']):
                status = 'default' if year['id'] == data['activeYear'] else 'archived' if year['archived'] else 'active'
                print(f"{year['id']}\t{year['label']}\t{year['organization']}\t{status}")
            return
        if args.command == 'add':
            add_year(data, args.year, args.term, args.organization)
        elif args.command == 'set-default':
            set_default(data, args.year_id)
        elif args.command in ('archive', 'unarchive'):
            archive_year(data, args.year_id, args.command == 'archive')
        else:
            remove_empty_year(data, args.year_id)
        validate(root, data)
        atomic_json(path, data)
        print('Year catalog updated.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
