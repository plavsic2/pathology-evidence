import csv
from pathlib import Path
import pandas as pd
import pytest
import copy
import json
import sys
from types import SimpleNamespace
from unittest.mock import patch
from evaluation.priority_cases import PRIORITY_CASES, select_queries


def test_priority_cases_are_validation_only_in_committed_manifest():
    manifest = pd.read_csv(Path(__file__).resolve().parents[1] / 'data/splits.csv')
    assert len(manifest) == 3150
    assert manifest.groupby(['label', 'split']).size().unstack().to_dict() == {
        'gallery': {c: 75 for c in manifest.label.unique()},
        'test': {c: 50 for c in manifest.label.unique()},
        'train': {c: 200 for c in manifest.label.unique()},
        'val': {c: 25 for c in manifest.label.unique()},
    }
    assert select_queries(manifest, query_ids=list(PRIORITY_CASES)) == list(PRIORITY_CASES)
    with pytest.raises(ValueError, match='missing'):
        select_queries(manifest, split='test', query_ids=list(PRIORITY_CASES))
    with pytest.raises(ValueError, match='missing'):
        select_queries(manifest, query_ids=['unknown'])


def test_partner_validation_table_and_manifest_agree():
    root = Path(__file__).resolve().parents[1]
    with (root / 'evaluation/validation_examples.csv').open() as f:
        rows = list(csv.DictReader(f))
    manifest = pd.read_csv(root / 'data/splits.csv')
    assert {r['image_id'] for r in rows} == set(manifest.loc[manifest.split == 'val', 'image_id'])
    assert sum(r['correct'] == 'True' for r in rows) == 215


def test_investigator_calls_existing_engine_for_priority_pair(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    root = Path(__file__).resolve().parents[1]
    base = json.loads((root / 'app/mock_response.json').read_text())
    calls = []
    def analyze(query_id, method):
        calls.append((query_id, method))
        response = copy.deepcopy(base)
        response['query']['image_id'] = query_id
        response['method'] = method
        return response
    engine = SimpleNamespace(df=pd.read_csv(root / 'data/splits.csv'), analyze_query=analyze)
    monkeypatch.setenv('REVIEW_BUNDLE_DIR', str(tmp_path))
    with patch.dict(sys.modules, {'src.engine': SimpleNamespace(load_engine=lambda: engine)}):
        app = AppTest.from_file(str(root / 'app/pages/2_Failure_review.py')).run(timeout=30)
        next(x for x in app.selectbox if x.label == 'Investigation source').set_value('Cached engine').run(timeout=30)
        assert not app.exception
        assert ('70eccc3f2e78b00d', 'class_aware') in calls
        assert ('70eccc3f2e78b00d', 'contrastive') in calls
        assert [x.value for x in app.subheader] == ['class_aware', 'contrastive']
        assert any('Handpicked investigation' in x.value for x in app.info)
