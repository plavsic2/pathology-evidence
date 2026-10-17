import copy
import json
import tempfile
import unittest
from pathlib import Path
from evaluation.evidence_export import case_html, summary_html
from evaluation.export_review import export
from evaluation.review import save_review, summarize


def pair():
    base = json.loads((Path(__file__).resolve().parents[1] / 'app/mock_response.json').read_text())
    other = copy.deepcopy(base)
    other['method'] = 'contrastive'
    return {'class_aware': base, 'contrastive': other}


class ExportTests(unittest.TestCase):
    def test_empty_summary_never_claims_a_result(self):
        output = summary_html(summarize([]))
        self.assertIn('No non-mock reviews collected', output)

    def test_evidence_text_is_escaped_and_fingerprinted(self):
        data = pair()
        for result in data.values():
            result['query']['image_id'] = '<script>bad()</script>'
        page = case_html(data)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('SHA-256', page)
        self.assertIn('Image unavailable', page)

    def test_export_excludes_mock_counts_and_escapes_formula_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'reviews.sqlite3'
            save_review(db, 'one', 'Team developer', pair(), 'tie', note='=1+1', mock=True)
            out = Path(tmp) / 'report'
            summary = export(db, out)
            self.assertEqual(summary['n_reviews'], 0)
            self.assertIn("'=1+1", (out / 'review_responses.csv').read_text())
            self.assertTrue((out / 'review_dashboard.html').is_file())
