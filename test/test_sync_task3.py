import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_task3', ROOT/'src/sync_task3.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def source():
    return {'read_errors': 0, 'student_repositories': 1, 'release_only': True,
            'students': [{'repository': 'ece281s1/Example123project', 'configuration': 'p3-release',
                          'status': 'complete_valid', 'verified_cases': 20, 'task3_cases': 20,
                          'task3_total_rounds': 100, 'task3_total_movement_steps': 170,
                          'generated_at': '2026-11-18 19:00:00', 'run_id': 'RUN1',
                          'issue_url': 'https://example.test/issues/1', 'commit': 'abcdef',
                          'released': True, 'release_event': 'release', 'release_tag': 'p3',
                          'release_workflow': 'release.yaml@refs/tags/p3'}]}


class SyncTests(unittest.TestCase):
    def test_complete_lengths_and_source_time(self):
        result = sync.make_snapshot(source())
        entry = result['entries'][0]
        self.assertEqual(entry['metrics'], {'rounds': 100, 'movementSteps': 170})
        self.assertEqual(entry['name'], 'Example')
        self.assertTrue(entry['submittedAt'].endswith('+08:00'))
        self.assertTrue(entry['released'])

    def test_failure_and_no_result_are_not_ranked_as_zero(self):
        for status in ('invalid_case', 'no_release_result', 'missing_task3'):
            data=source(); data['students'][0]['status']=status
            self.assertEqual(sync.make_snapshot(data)['entries'], [])

    def test_preview_and_unverified_complete_results_are_rejected(self):
        data=source(); data['release_only']=False
        with self.assertRaises(ValueError):sync.make_snapshot(data)
        for key,value in [('configuration','p3'),('released',None),('release_event','push'),
                          ('release_workflow','push.yaml@refs/tags/p3')]:
            data=source(); data['students'][0][key]=value
            with self.assertRaises(ValueError):sync.make_snapshot(data)

    def test_stale_and_partial_reads_are_rejected(self):
        data=source(); data['read_errors']=1
        with self.assertRaises(ValueError): sync.make_snapshot(data)
        data=source(); data['students'][0]['status']='stale_after_read_error'
        with self.assertRaises(ValueError): sync.make_snapshot(data)

    def test_complete_status_requires_integer_lengths_and_twenty_cases(self):
        for key,value in [('verified_cases',19),('task3_cases',19),('task3_total_rounds',None),
                          ('task3_total_movement_steps',1.5),('task3_total_rounds',True)]:
            data=source(); data['students'][0][key]=value
            with self.assertRaises(ValueError):sync.make_snapshot(data)

    def test_latest_run_wins_even_if_latest_failed(self):
        data=source(); row=copy.deepcopy(data['students'][0]);row.update(configuration='p3-release',generated_at='2026-11-18 20:00:00',status='invalid_case')
        data['students'].append(row)
        self.assertEqual(sync.make_snapshot(data)['entries'],[])

    def test_publication_refuses_unrelated_staged_files(self):
        def fake_git(root,*args):
            if args==('branch','--show-current'):return 'main'
            if args==('remote','get-url','origin'):return 'https://github.com/Doyona/SJTU-GC-ECE2810J-26FA.git'
            if args==('diff','--cached','--name-only'):return 'unrelated.txt'
            return ''
        with patch.object(sync,'git',side_effect=fake_git):
            with self.assertRaisesRegex(RuntimeError,'staged'):
                sync.check_checkout(ROOT)

    def test_atomic_update_preserves_other_projects_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'site/data').mkdir(parents=True)
            shutil.copyfile(ROOT/'site/leaderboard.mjs',root/'site/leaderboard.mjs')
            baseline={'demo':False,'updatedAt':'2026-11-01T00:00:00Z','projects':[{
                'id':'extra-project','title':'Extra','description':'Preserved','primaryMetric':'steps',
                'metrics':[{'key':'steps','label':'Steps','unit':'','direction':'asc','decimals':0}],
                'entries':[{'id':'baseline','name':'Baseline','metrics':None}]}]}
            path=root/'site/data/leaderboard.json';path.write_text(json.dumps(baseline))
            self.assertTrue(sync.update_files(root,source()))
            first=path.read_bytes()
            self.assertFalse(sync.update_files(root,source()))
            self.assertEqual(path.read_bytes(),first)
            self.assertEqual(json.loads(first)['projects'][0],baseline['projects'][0])
            data=source();data['read_errors']=1
            with self.assertRaises(ValueError):sync.update_files(root,data)
            self.assertEqual(path.read_bytes(),first)


if __name__ == '__main__':unittest.main()
