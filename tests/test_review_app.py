"""Streamlit behavior checks, runnable without CONCH or engine dependencies."""
import os
import tempfile
import unittest
from pathlib import Path
try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


@unittest.skipIf(AppTest is None, 'Streamlit test support is not installed')
class ReviewAppTests(unittest.TestCase):
    def test_blinding_submission_and_missing_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get('REVIEW_DB')
            os.environ['REVIEW_DB'] = tmp + '/reviews.sqlite3'
            try:
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app/streamlit_app.py')).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertFalse(app.json)
                self.assertFalse(any(c.label == 'Reveal dataset label' for c in app.checkbox))
                app.checkbox[0].check().run(timeout=30)
                app.radio[0].set_value('tie')
                app.button[0].click().run(timeout=30)
                self.assertEqual(len(app.success), 1)
                app.toggle[0].set_value(False).run(timeout=30)
                self.assertFalse(app.exception)
                app.toggle[0].set_value(True).run(timeout=30)
                self.assertTrue(app.button[0].disabled)
                next(x for x in app.selectbox if x.label == 'Data source').set_value('Saved response pairs').run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(app.info)
            finally:
                if old is None:
                    os.environ.pop('REVIEW_DB', None)
                else:
                    os.environ['REVIEW_DB'] = old

    def test_failure_page_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get('REVIEW_BUNDLE_DIR')
            os.environ['REVIEW_BUNDLE_DIR'] = tmp
            try:
                path = str(Path(__file__).resolve().parents[1] / 'app/pages/2_Failure_review.py')
                app = AppTest.from_file(path).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(app.info)
                self.assertTrue(app.warning)
            finally:
                if old is None:
                    os.environ.pop('REVIEW_BUNDLE_DIR', None)
                else:
                    os.environ['REVIEW_BUNDLE_DIR'] = old

    def test_reviewer_entrypoint_has_no_exploration_or_investigator_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.environ.get('REVIEW_DB')
            os.environ['REVIEW_DB'] = tmp + '/reviews.sqlite3'
            try:
                path = str(Path(__file__).resolve().parents[1] / 'app/reviewer_app.py')
                app = AppTest.from_file(path).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertFalse(app.toggle)
                self.assertFalse(app.json)
                source = next(x for x in app.selectbox if x.label == 'Data source')
                self.assertEqual(source.options, ['Demonstration', 'Saved response pairs'])
                self.assertTrue(app.button[0].disabled)
                app.checkbox[0].check().run(timeout=30)
                self.assertFalse(app.button[0].disabled)
            finally:
                if previous is None:
                    os.environ.pop('REVIEW_DB', None)
                else:
                    os.environ['REVIEW_DB'] = previous
