import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
from evaluation.prepare_cohort import prepare
from evaluation.review import fingerprint


def test_full_pool_selection_portable_hashes_and_immutability(tmp_path):
    root = Path(__file__).resolve().parents[1]
    base = json.loads((root / 'app/mock_response.json').read_text())
    rows = []
    def item(image_id, label, split):
        path = tmp_path / (image_id + '.bin')
        path.write_bytes(image_id.encode())
        rows.append(dict(image_id=image_id, label=label, split=split,
                         relative_path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        return dict(image_id=image_id, image_path=str(path), class_id=label)
    for prediction in base['predictions']:
        for i, ref in enumerate(prediction['references']):
            ref.update(item(prediction['class_id'] + str(i), prediction['class_id'], 'gallery'))
    queries = {}
    for i in range(9):
        q = item('query' + str(i), base['predictions'][0]['class_id'], 'val')
        queries[q['image_id']] = dict(image_id=q['image_id'], image_path=q['image_path'], ground_truth=q['class_id'])
    def analyze(qid, method):
        result = copy.deepcopy(base)
        result.update(query=queries[qid], method=method)
        return result
    frame = pd.DataFrame(rows)
    manifest = tmp_path / 'splits.csv'
    frame.to_csv(manifest, index=False)
    output = tmp_path / 'frozen'
    plan = prepare(SimpleNamespace(df=frame, analyze_query=analyze), manifest, output, count=6)
    assert plan['pool_size'] == 9
    assert [c['cohort'] for c in plan['cases']].count('random') == 4
    assert [c['cohort'] for c in plan['cases']].count('difficult') == 2
    assert (output / 'splits.csv').read_bytes() == manifest.read_bytes()
    for case in plan['cases']:
        pair = json.loads((output / case['file']).read_text())
        assert fingerprint(pair) == case['bundle_sha256']
        assert not Path(pair['class_aware']['query']['image_path']).is_absolute()
    with pytest.raises(FileExistsError):
        prepare(SimpleNamespace(df=frame), manifest, output)
