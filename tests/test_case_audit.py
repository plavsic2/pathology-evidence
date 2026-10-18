import csv
import copy
import json
import tempfile
import unittest
from pathlib import Path
from evaluation.case_audit import audit_case, verify_manifest


def pair():
    a = json.loads((Path(__file__).resolve().parents[1] / 'app/mock_response.json').read_text())
    b = copy.deepcopy(a)
    b['method'] = 'contrastive'
    return {'class_aware': a, 'contrastive': b}


class AuditTests(unittest.TestCase):
    def test_failure_categories_and_overlap(self):
        data = pair()
        self.assertTrue(audit_case(data)['identical_reference_sets'])
        self.assertTrue(audit_case(data)['correct'])
        for result in data.values():
            result['query']['ground_truth'] = 'ADI'
        self.assertFalse(audit_case(data)['correct'])
        self.assertFalse(audit_case(data)['truth_in_candidates'])

    def test_gallery_provenance_and_cross_partition_hashes(self):
        data = pair()
        a = data['class_aware']
        rows = [{'image_id': a['query']['image_id'], 'relative_path': 'q.png', 'label': 'TUM', 'split': 'val', 'sha256': 'q'}]
        for p in a['predictions']:
            rows.extend({'image_id': r['image_id'], 'relative_path': r['image_id']+'.png', 'label': r['class_id'], 'split': 'gallery', 'sha256': r['image_id']} for r in p['references'])
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'splits.csv'
            def write():
                with manifest.open('w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            write()
            self.assertTrue(verify_manifest(data, manifest)['passed'])
            rows[1]['split'] = 'train'
            rows[1]['sha256'] = 'q'
            write()
            result = verify_manifest(data, manifest)
            self.assertFalse(result['passed'])
            self.assertGreaterEqual(len(result['errors']), 2)
