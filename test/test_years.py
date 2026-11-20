import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from sync_task3 import update_files
from year_catalog import add_year, archive_year, catalog, find_year, remove_empty_year, set_default, validate
from test_sync_task3 import source


def legacy():
    return {'demo': False, 'updatedAt': '2026-11-19T00:00:00Z', 'projects': [{
        'id': 'project-03', 'title': 'Task 3', 'description': 'Results', 'primaryMetric': 'rounds',
        'metrics': [{'key': 'rounds', 'label': 'Rounds', 'unit': '', 'direction': 'asc', 'decimals': 0}],
        'entries': [{'id': 'student', 'name': 'Student', 'metrics': {'rounds': 200}}]}]}


class YearTests(unittest.TestCase):
    def test_management_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'site/data').mkdir(parents=True)
            shutil.copyfile(ROOT/'site/leaderboard.mjs',root/'site/leaderboard.mjs')
            original = catalog(legacy())
            path = root/'site/data/leaderboard.json'; path.write_text(json.dumps(original))
            def command(*args):
                return subprocess.run([sys.executable,'-B',str(ROOT/'src/manage_years.py'),
                                       '--website-root',str(root),*args],capture_output=True,text=True)
            self.assertEqual(command('add','--year','2027','--term','fall','--organization','course27').returncode,0)
            self.assertEqual(command('set-default','2027-fall').returncode,0)
            self.assertEqual(command('archive','2026-fall').returncode,0)
            before=path.read_bytes()
            self.assertNotEqual(command('remove-empty','2026-fall').returncode,0)
            self.assertEqual(path.read_bytes(),before)
            self.assertIn('archived',command('list').stdout)
            self.assertEqual(command('unarchive','2026-fall').returncode,0)
            self.assertEqual(command('set-default','2026-fall').returncode,0)
            self.assertEqual(command('remove-empty','2027-fall').returncode,0)
            self.assertEqual(json.loads(path.read_text()),original)

    def test_migration_preserves_existing_results(self):
        original = legacy()
        result = catalog(copy.deepcopy(original))
        self.assertEqual(find_year(result, '2026-fall')['projects'], original['projects'])
        self.assertEqual(result['activeYear'], '2026-fall')

    def test_new_year_has_no_copied_results(self):
        data = catalog(legacy())
        add_year(data, 2027, 'spring', 'course27')
        self.assertEqual(find_year(data, '2027-spring')['projects'][0]['entries'], [])
        self.assertEqual(len(find_year(data, '2026-fall')['projects'][0]['entries']), 1)
        with self.assertRaises(ValueError): add_year(data, 2027, 'spring', 'course27')

    def test_archive_and_removal_preserve_populated_years(self):
        data = catalog(legacy())
        with self.assertRaises(ValueError): archive_year(data, '2026-fall')
        with self.assertRaises(ValueError): remove_empty_year(data, '2026-fall')
        add_year(data, 2027, 'fall', 'course27'); set_default(data, '2027-fall')
        archive_year(data, '2026-fall')
        with self.assertRaises(ValueError): set_default(data, '2026-fall')
        with self.assertRaises(ValueError): remove_empty_year(data, '2026-fall')
        archive_year(data, '2026-fall', False); set_default(data, '2026-fall')
        remove_empty_year(data, '2027-fall')
        self.assertEqual(len(data['years']), 1)

    def test_sync_changes_only_its_year_even_if_default_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'site/data').mkdir(parents=True)
            shutil.copyfile(ROOT/'site/leaderboard.mjs', root/'site/leaderboard.mjs')
            data = catalog(legacy()); add_year(data, 2027, 'fall', 'course27')
            set_default(data, '2027-fall')
            untouched = copy.deepcopy(find_year(data, '2027-fall'))
            path = root/'site/data/leaderboard.json'; path.write_text(json.dumps(data))
            self.assertTrue(update_files(root, source()))
            after = json.loads(path.read_text())
            self.assertEqual(after['activeYear'], '2027-fall')
            self.assertEqual(find_year(after, '2027-fall'), untouched)
            self.assertEqual(find_year(after, '2026-fall')['projects'][0]['entries'][0]['metrics']['rounds'], 100)
            self.assertFalse(update_files(root, source()))
            before = path.read_bytes()
            with self.assertRaises(ValueError): update_files(root, source(), '2027-fall')
            self.assertEqual(path.read_bytes(), before)
            archive_year(after, '2026-fall'); path.write_text(json.dumps(after))
            before = path.read_bytes()
            with self.assertRaises(ValueError): update_files(root, source())
            self.assertEqual(path.read_bytes(), before)

    def test_different_organization_can_sync_only_to_its_own_year(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'site/data').mkdir(parents=True)
            shutil.copyfile(ROOT/'site/leaderboard.mjs', root/'site/leaderboard.mjs')
            data=catalog(legacy()); add_year(data,2027,'fall','course27')
            path=root/'site/data/leaderboard.json'; path.write_text(json.dumps(data))
            current=copy.deepcopy(find_year(data,'2026-fall'))
            report=source(); report['students'][0]['repository']='course27/Example123project'
            self.assertTrue(update_files(root,report,'2027-fall','course27'))
            self.assertEqual(find_year(json.loads(path.read_text()),'2026-fall'),current)
            validate(root,json.loads(path.read_text()))


if __name__ == '__main__': unittest.main()
