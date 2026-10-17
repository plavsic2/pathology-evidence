"""End-to-end reviewer protocol with temporary abstract images only."""
import copy
import csv
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
try:
    from streamlit.testing.v1 import AppTest
    from PIL import Image
except ImportError:
    AppTest = None
from evaluation.review_plan import freeze_plan
from evaluation.review import read_reviews


@unittest.skipIf(AppTest is None, 'Streamlit test support unavailable')
class ProtocolIntegrationTests(unittest.TestCase):
    def test_practice_frozen_plan_skip_and_tamper_detection(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / 'bundles'
            folder.mkdir()
            template = json.loads((repo / 'app/mock_response.json').read_text())
            rows = []
            def asset(image_id, label, split):
                filename = image_id + '.png'
                path = folder / filename
                Image.new('RGB', (24,24), (len(rows)*25, 40, 60)).save(path)
                rows.append({'image_id':image_id,'relative_path':filename,'label':label,'split':split,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
                return filename
            for p in template['predictions']:
                for ref in p['references']:
                    ref['image_path'] = asset(ref['image_id'], ref['class_id'], 'gallery')
            for i in range(4):
                base = copy.deepcopy(template)
                base['query']['image_id'] = f'query{i}'
                base['query']['image_path'] = asset(f'query{i}', 'TUM', 'val')
                other = copy.deepcopy(base)
                other['method'] = 'contrastive'
                (folder / f'case_{i:03d}.json').write_text(json.dumps({'class_aware':base,'contrastive':other}))
            manifest = root / 'splits.csv'
            with manifest.open('w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(rows)
            plan = freeze_plan(folder, manifest, count=4)
            self.assertEqual(len(plan['cases']), 4)
            self.assertEqual(sum(c['cohort']=='random' for c in plan['cases']), 3)
            plan_path = root / 'plan.json'
            plan_path.write_text(json.dumps(plan))
            db = root / 'review.sqlite3'
            settings = {'REVIEW_BUNDLE_DIR':str(folder),'REVIEW_PLAN':str(plan_path),'SPLIT_MANIFEST':str(manifest),'REVIEW_DB':str(db),'REVIEW_SPLIT':'val'}
            old = {k:os.environ.get(k) for k in settings}
            os.environ.update(settings)
            try:
                app = AppTest.from_file(str(repo / 'app/reviewer_app.py')).run(timeout=30)
                app.checkbox[0].check().run(timeout=30)
                app.radio[0].set_value('tie')
                next(b for b in app.button if b.label=='Save review').click().run(timeout=30)
                self.assertTrue(app.success)
                next(s for s in app.selectbox if s.label=='Data source').set_value('Saved response pairs').run(timeout=30)
                self.assertFalse(app.exception)
                self.assertFalse(next(b for b in app.button if b.label=='Save review').disabled)
                next(b for b in app.button if b.label=='Skip this trial').click().run(timeout=30)
                self.assertTrue(any(r['choice']=='skip' and not r['mock'] for r in read_reviews(db)))
                self.assertTrue(any('1 skipped' in x.value for x in app.markdown))
                corrupt = folder / rows[0]['relative_path']
                original_bytes = corrupt.read_bytes()
                corrupt.write_bytes(b'invalid-image')
                app.run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(next(b for b in app.button if b.label=='Save review').disabled)
                self.assertFalse(next(b for b in app.button if b.label=='Skip this trial').disabled)
                corrupt.write_bytes(original_bytes)
                next(s for s in app.selectbox if s.label=='Case').set_value(1).run(timeout=30)
                self.assertIsNone(app.radio[0].value)
                # Changing even one frozen pair must be detected when its trial opens.
                trial_select = next(s for s in app.selectbox if s.label=='Case')
                for p in folder.glob('case_*.json'):
                    data=json.loads(p.read_text())
                    for r in data.values():
                        r['query']['ground_truth']='ADI'
                    p.write_text(json.dumps(data))
                app.run(timeout=30)
                self.assertTrue(app.error)
                self.assertFalse(app.exception)
            finally:
                for k,v in old.items():
                    if v is None:
                        os.environ.pop(k,None)
                    else:
                        os.environ[k]=v
