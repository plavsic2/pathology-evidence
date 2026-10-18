import copy
import json
import tempfile
import unittest
from pathlib import Path
from evaluation.review import assignment, blinded_view, read_reviews, save_review, summarize, validate_pair


def pair():
    root = Path(__file__).resolve().parents[1]
    a = json.loads((root / 'app/mock_response.json').read_text())
    b = copy.deepcopy(a)
    b['method'] = 'contrastive'
    return {'class_aware': a, 'contrastive': b}


class ReviewTests(unittest.TestCase):
    def test_assignment_stable_and_contains_both_methods(self):
        self.assertEqual(assignment('reviewer-1', pair()), assignment('reviewer-1', pair()))
        self.assertEqual(set(assignment('reviewer-1', pair()).values()), {'class_aware', 'contrastive'})

    def test_reject_different_queries_predictions_counts_and_classes(self):
        mutations = [lambda b: b['query'].update(image_id='different'),
                     lambda b: b['predictions'][0].update(score=0.1),
                     lambda b: b['predictions'][0].update(references=[]),
                     lambda b: b['predictions'][0]['references'][0].update(class_id='ADI')]
        for mutate in mutations:
            data = pair()
            mutate(data['contrastive'])
            with self.assertRaises(ValueError):
                validate_pair(data)

    def test_public_view_excludes_answers_and_rankings(self):
        view = blinded_view(pair()['class_aware'])
        self.assertEqual(set(view[0]), {'class_id', 'reference_count'})

    def test_resubmission_replaces_and_mock_reviews_are_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'reviews.sqlite3'
            save_review(db, 'one', 'Team developer', pair(), 'A', mock=True)
            save_review(db, 'one', 'Team developer', pair(), 'tie', mock=True)
            self.assertEqual(len(read_reviews(db)), 1)
            summary = summarize(read_reviews(db))
            self.assertEqual(summary['n_reviews'], 0)
            self.assertEqual(summary['excluded_mock_reviews'], 1)
            save_review(db, 'two', 'Pathology expert', pair(), 'neither', mock=False)
            self.assertEqual(summarize(read_reviews(db))['counts']['neither'], 1)


if __name__ == '__main__':
    unittest.main()
