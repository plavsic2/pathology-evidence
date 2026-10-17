import copy
import json
import tempfile
import unittest
from pathlib import Path
from evaluation.review import assignment, save_review, read_reviews, summarize, mark_ready, is_ready, fingerprint
from evaluation.review_plan import schedule, completion


def pair():
    a = json.loads((Path(__file__).resolve().parents[1] / 'app/mock_response.json').read_text())
    b = copy.deepcopy(a)
    b['method'] = 'contrastive'
    return {'class_aware': a, 'contrastive': b}


class PlanTests(unittest.TestCase):
    def test_schedule_stable_repeats_separated_and_small_pool_has_none(self):
        cases = [{'file': str(i), 'cohort': 'random'} for i in range(8)]
        trials = schedule(cases, 'one', 2)
        self.assertEqual(trials, schedule(cases, 'one', 2))
        self.assertEqual(len(trials), 10)
        by_id = {t['trial_id']: i for i,t in enumerate(trials)}
        for i,t in enumerate(trials):
            if t['repeat_of']:
                self.assertGreaterEqual(i - by_id[t['repeat_of']], 4)
        self.assertEqual(len(schedule(cases[:3], 'one')), 3)

    def test_repeat_kept_separate_and_compared_by_method_not_letter(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'reviews.db'
            data = pair()
            original = {'trial_id': 'original-0', 'repeat_of': None, 'cohort': 'random'}
            repeat = {'trial_id': 'repeat-0', 'repeat_of': 'original-0', 'cohort': 'random'}
            for trial in [original, repeat]:
                choice = next(k for k,v in assignment('s', data, trial['trial_id']).items() if v == 'contrastive')
                save_review(db,'s','Pathology expert',data,choice,trial=trial,protocol_hash='p',misleading=choice)
            result = summarize(read_reviews(db))
            self.assertEqual(result['n_reviews'], 1)
            self.assertEqual(result['counts']['contrastive'], 1)
            self.assertEqual(result['repeat_pairs_compared'], 1)
            self.assertEqual(result['repeat_pairs_agree'], 1)
            self.assertEqual(result['misleading_counts']['contrastive'], 1)

    def test_skip_and_completion_and_protocol_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'reviews.db'
            trial = {'trial_id': 'original-0', 'repeat_of': None}
            save_review(db,'s','Other',pair(),'skip',trial=trial,protocol_hash='p')
            records = read_reviews(db)
            result = completion([trial, {'trial_id':'original-1'}],records,'s','p')
            self.assertEqual(result, {'completed':0,'skipped':1,'unanswered':1,'total':2})
            self.assertEqual(summarize(records)['n_reviews'], 0)
            save_review(db,'s','Other',pair(),'tie',trial=trial,protocol_hash='different')
            self.assertEqual(len(read_reviews(db)),2)

    def test_practice_readiness_persists_and_missing_db_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'reviews.db'
            self.assertEqual(read_reviews(db), [])
            self.assertFalse(is_ready(db, 's', '1.1'))
            mark_ready(db, 's', '1.1')
            self.assertTrue(is_ready(db, 's', '1.1'))
            self.assertFalse(is_ready(db, 'different', '1.1'))
