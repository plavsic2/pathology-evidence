import copy
import json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from streamlit.testing.v1 import AppTest


def test_visual_evidence_success_partial_failure_and_no_repeat_calls(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    base = json.loads((root / 'app/mock_response.json').read_text())
    Image.new('RGB', (224,224), 'pink').save(tmp_path / 'tile.png')
    base['query']['image_path'] = 'tile.png'
    for candidate in base['predictions']:
        ref = candidate['references'][0]
        ref['image_path'] = 'tile.png'
        candidate['references'] = [dict(ref, image_id=ref['image_id']+str(i)) for i in range(3)]
    base['method'] = 'contrastive'
    (tmp_path / 'case_0001.json').write_text(json.dumps({'contrastive': base, 'class_aware': base}))
    monkeypatch.setenv('EVIDENCE_BUNDLE_DIR',str(tmp_path))
    monkeypatch.setenv('EVIDENCE_SNAPSHOT_DIR',str(tmp_path/'snapshots'))
    monkeypatch.setenv('LUMEN_API_KEY','test-placeholder-not-a-key')
    def explain(analysis, max_refs):
        assert max_refs == 3
        assert all(len(p['references']) == 3 for p in analysis['predictions'])
        return {'query': analysis['query'], 'candidates': [dict(class_id=p['class_id'],references=p['references'],supporting=['Image A and C share similar arrangement.'] if i else [],contrasting=['Different density.'],explanation_unavailable=i==1) for i,p in enumerate(analysis['predictions'])]}
    with patch('src.evidence_explainer.explain_candidates',side_effect=explain) as call:
        app=AppTest.from_file(str(root/'app/evidence_app.py')).run(timeout=30)
        assert not app.exception
        assert len(app.get('image')) == 12  # main images, pinned sidebar query, inspector
        assert not app.json
        assert not any('CONCH' in m.value or 'gemma' in m.value or '0.858' in m.value for m in app.markdown)
        app.button[0].click().run(timeout=30)
        assert not app.exception
        assert call.call_count==1
        assert any('No specific supporting' in m.value for m in app.markdown)
        assert len([w for w in app.warning if w.value=='Visual explanation temporarily unavailable'])==1
        assert any('**Query (A)**' in m.value and '**Reference C**' in m.value for m in app.markdown)
        next(b for b in app.button if b.label=='Save observations for offline replay').click().run(timeout=30)
        assert len(list((tmp_path/'snapshots').glob('*.json')))==1
        replay=AppTest.from_file(str(root/'app/evidence_app.py')).run(timeout=30)
        assert not replay.exception
        assert any('local saved copy' in c.value for c in replay.caption)
        assert call.call_count==1
        app.slider[0].set_value(700).run(timeout=30)
        assert call.call_count==1
        next(b for b in app.button if b.label=='Enlarge Image B').click().run(timeout=30)
        assert not app.exception
        assert call.call_count==1
        assert any('224 x 224' in c.value for c in app.caption)
        assert any('does not upload' in c.value for c in app.caption)


def test_visual_evidence_missing_key_and_total_failure(tmp_path, monkeypatch):
    root=Path(__file__).resolve().parents[1]
    base=json.loads((root/'app/mock_response.json').read_text())
    Image.new('RGB',(224,224),'pink').save(tmp_path/'tile.png')
    base['query']['image_path']='tile.png'
    for p in base['predictions']:
        p['references']=[dict(p['references'][0],image_path='tile.png') for _ in range(3)]
    (tmp_path/'case_0001.json').write_text(json.dumps({'contrastive':base,'class_aware':base}))
    monkeypatch.setenv('EVIDENCE_BUNDLE_DIR',str(tmp_path))
    monkeypatch.setenv('EVIDENCE_SNAPSHOT_DIR',str(tmp_path/'snapshots'))
    monkeypatch.delenv('LUMEN_API_KEY',raising=False)
    app=AppTest.from_file(str(root/'app/visual_evidence.py')).run(timeout=30)
    assert app.button[0].disabled
    monkeypatch.setenv('LUMEN_API_KEY','test-placeholder-not-a-key')
    with patch('src.evidence_explainer.explain_candidates',side_effect=RuntimeError('sensitive diagnostic')):
        app.run(timeout=30)
        app.button[0].click().run(timeout=30)
        assert not app.exception
        assert len(app.get('image'))==12
        assert not any('sensitive diagnostic' in m.value for m in app.markdown)
