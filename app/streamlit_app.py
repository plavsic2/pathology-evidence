"""Comparison UI; consumes the unchanged analyze_query response."""
import copy
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.review import assignment, fingerprint, save_review, validate_pair
from evaluation.case_audit import verify_manifest
NAMES = json.loads((ROOT / 'config/classes.json').read_text())["names"]
st.set_page_config(page_title="Tissue Evidence Explorer", layout="wide")
st.title("Tissue Evidence Explorer")
st.caption("Compare tissue categories using reference examples. Research prototype.")

def fixture(seed):
    colors = ['#bdc8d7', '#d3c2d4', '#a8c9c2']
    shapes = ''.join(f'<circle cx="{30+i*35}" cy="{50+(i%2)*45}" r="18" fill="{colors[(seed+i)%3]}"/>' for i in range(5))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="150"><rect width="240" height="150" fill="#f2f4f7"/>{shapes}<text x="12" y="139" font-size="12">Layout fixture - not tissue</text></svg>'

source = st.sidebar.selectbox('Data source', ['Demonstration', 'Saved response pairs', 'Cached engine'])
mock = source == 'Demonstration'
asset_root = ROOT
if mock:
    base = json.loads((ROOT / 'app/mock_response.json').read_text())
    other = copy.deepcopy(base)
    other['method'] = 'contrastive'
    bundle = {'class_aware': base, 'contrastive': other}
    st.warning('DEMONSTRATION: abstract fixtures and fabricated scores. Both methods have identical references. No pathology findings.')
elif source == 'Saved response pairs':
    folder = Path(os.environ.get('REVIEW_BUNDLE_DIR', str(ROOT / 'artifacts/review_bundles')))
    paths = sorted(folder.glob('*.json')) if folder.is_dir() else []
    if not paths:
        st.info('No saved pairs found. See presentation/person2-review-guide.md.')
        st.stop()
    selected = st.sidebar.selectbox('Case', range(len(paths)), format_func=lambda i: f'Case {i+1:03d}')
    try:
        bundle = json.loads(paths[selected].read_text())
        asset_root = folder
    except (OSError, ValueError) as exc:
        st.error(f'Could not read pair: {exc}')
        st.stop()
else:
    @st.cache_resource
    def get_engine():
        from src.engine import load_engine
        return load_engine()
    try:
        engine = get_engine()
        ids = engine.df.loc[engine.df.split == 'val', 'image_id'].tolist()
        if not ids:
            raise ValueError('No validation queries')
        selected = st.sidebar.selectbox('Case', range(len(ids)), format_func=lambda i: f'Case {i+1:03d}')
        bundle = {m: engine.analyze_query(ids[selected], method=m) for m in ('class_aware', 'contrastive')}
    except Exception as exc:
        st.error(f'Cached engine unavailable: {exc}')
        st.info('Use Demonstration or Saved response pairs. No live CONCH call is needed.')
        st.stop()
try:
    validate_pair(bundle)
except (KeyError, TypeError, ValueError) as exc:
    st.error(f'Incomparable responses: {exc}')
    st.stop()

def image_data(path):
    if not path:
        return None
    p = Path(path)
    p = p if p.is_absolute() else asset_root / p
    try:
        return p.read_bytes() if p.is_file() else None
    except OSError:
        return None

missing = not mock and any(image_data(item['image_path']) is None for result in bundle.values() for item in [result['query']] + [r for c in result['predictions'] for r in c['references']])
if missing:
    st.error('Images are missing. Submission is disabled until all query and reference images are available.')
provenance_ok = mock
if not mock:
    manifest = Path(os.environ.get('SPLIT_MANIFEST', str(ROOT / 'data/splits.csv')))
    if manifest.is_file():
        try:
            checked = verify_manifest(bundle, manifest, asset_root, allowed_split=os.environ.get('REVIEW_SPLIT', 'val'))
            provenance_ok = checked['passed']
        except (ValueError, KeyError, OSError, TypeError):
            provenance_ok = False
    if not provenance_ok:
        st.warning('Review saving requires the agreed split manifest and matching gallery/query labels. Configure SPLIT_MANIFEST. Development defaults to validation queries.')
if 'review_session' not in st.session_state:
    st.session_state.review_session = uuid.uuid4().hex
session = st.sidebar.text_input('Anonymous reviewer session', value=st.session_state.review_session)
role = st.sidebar.selectbox('Reviewer role', ['Team developer', 'Pathology trainee', 'Pathology expert', 'Other'])
blinded = st.sidebar.toggle('Blinded comparison', value=True)
mapping = assignment(session, bundle)
first = bundle['class_aware']
digest = fingerprint(bundle)
exposed = st.session_state.setdefault('exposed_cases', set())
if not blinded:
    exposed.add(digest)
st.subheader('Query image')
data = image_data(first['query']['image_path'])
if data:
    st.image(data, width=240)
elif mock:
    st.image(fixture(1), width=240)
if not blinded:
    st.info('Exploration mode is unblinded. Review submission is unavailable.')
    st.write('Candidate scores', [{'class': p['class_id'], 'score': p['score']} for p in first['predictions']])
    st.caption('Classifier scores are not calibrated clinical probabilities.')
    if st.checkbox('Reveal dataset label'):
        st.write(first['query'].get('ground_truth', 'Unavailable'))
st.subheader('Compare reference sets')
st.write('Which set better helps you compare these candidate tissue categories?')
for col, side in zip(st.columns(2), ('A', 'B')):
    with col:
        result = bundle[mapping[side]]
        st.markdown(f'### Set {side}' + (f' ({mapping[side]})' if not blinded else ''))
        for p in sorted(result['predictions'], key=lambda x: x['class_id']):
            st.markdown(f"**{NAMES.get(p['class_id'], p['class_id'])}**")
            for i, ref in enumerate(p['references']):
                data = image_data(ref['image_path'])
                if data:
                    st.image(data, width=180)
                elif mock:
                    st.image(fixture(i+2), width=180)
                else:
                    st.warning('Reference unavailable')
                st.caption(f'Reference {i+1}')
if blinded:
    if digest in exposed:
        st.warning('This case was already unblinded in this browser session. Use an unseen case for review.')
    with st.form('reference_review'):
        choice = st.radio('Preference', ['A', 'B', 'tie', 'neither'], index=None)
        note = st.text_area('Why? Optional. Do not enter identifying or patient information.', max_chars=2000)
        submitted = st.form_submit_button('Save review', disabled=bool(missing) or not provenance_ok or digest in exposed)
    if submitted:
        if choice is None or not session.strip():
            st.error('Choose a preference and provide an anonymous session ID.')
        else:
            try:
                db = Path(os.environ.get('REVIEW_DB', str(ROOT / 'artifacts/reviews.sqlite3')))
                save_review(db, session, role, bundle, choice, note, mock)
                st.success('Review saved. Resubmission replaces your response for this exact case.')
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(f'Could not save review: {exc}')
st.caption('References do not prove classifier reasoning or diagnosis. Blinding is a workflow aid, not a security boundary.')
