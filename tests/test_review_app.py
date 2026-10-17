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
                self.assertFalse(app.checkbox)
                app.radio[0].set_value('tie')
                app.button[0].click().run(timeout=30)
                self.assertEqual(len(app.success), 1)
                app.toggle[0].set_value(False).run(timeout=30)
                self.assertFalse(app.exception)
                app.toggle[0].set_value(True).run(timeout=30)
                self.assertTrue(app.button[0].disabled)
                app.selectbox[0].set_value('Saved response pairs').run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(app.info)
            finally:
                if old is None:
                    os.environ.pop('REVIEW_DB', None)
                else:
                    os.environ['REVIEW_DB'] = old
