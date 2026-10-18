"""Comparison UI; consumes the unchanged analyze_query response."""
import copy
import hashlib
import io
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.theme import apply_theme
from evaluation.review import assignment, fingerprint, save_review, validate_pair, read_reviews, mark_ready, is_ready
from evaluation.case_audit import verify_manifest
from evaluation.review_plan import schedule, completion, plan_hash
NAMES = json.loads((ROOT / 'config/classes.json').read_text())["names"]
st.set_page_config(page_title="Tissue Evidence Explorer", layout="wide")
apply_theme()
st.title("Tissue Evidence Explorer")
st.caption("Compare tissue categories using reference examples. Research prototype.")

def fixture(seed):
    colors = ['#bdc8d7', '#d3c2d4', '#a8c9c2']
    shapes = ''.join(f'<circle cx="{30+i*35}" cy="{50+(i%2)*45}" r="18" fill="{colors[(seed+i)%3]}"/>' for i in range(5))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="150"><rect width="240" height="150" fill="#f2f4f7"/>{shapes}<text x="12" y="139" font-size="12">Layout fixture - not tissue</text></svg>'

reviewer_only = st.session_state.get('reviewer_only', False)
source = st.sidebar.selectbox('Data source', ['Demonstration', 'Saved response pairs'] if reviewer_only else ['Demonstration', 'Saved response pairs', 'Cached engine'])
mock = source == 'Demonstration'
asset_root = ROOT
if 'review_session' not in st.session_state:
    st.session_state.review_session = uuid.uuid4().hex
session = st.sidebar.text_input('Anonymous reviewer session', value=st.session_state.review_session)
role = st.sidebar.selectbox('Reviewer role', ['Team developer', 'Pathology trainee', 'Pathology expert', 'Other'])
db = Path(os.environ.get('REVIEW_DB', str(ROOT / 'artifacts/reviews.sqlite3')))
protocol_hash = 'exploratory'
trials = []
trial = {}
image_size = st.sidebar.slider('Reference image size', 140, 340, 180, 20)
if mock:
    base = json.loads((ROOT / 'app/mock_response.json').read_text())
    other = copy.deepcopy(base)
    other['method'] = 'contrastive'
    bundle = {'class_aware': base, 'contrastive': other}
    st.warning('DEMONSTRATION: abstract fixtures and fabricated scores. Both methods have identical references. No pathology findings.')
elif source == 'Saved response pairs':
    folder = Path(os.environ.get('REVIEW_BUNDLE_DIR', str(ROOT / 'artifacts/review_bundles')))
    paths = sorted(p for p in folder.glob('*.json') if p.name != 'review_plan.json') if folder.is_dir() else []
    if not paths:
        st.info('No saved pairs found. See presentation/person2-review-guide.md.')
        st.stop()
    plan_path = Path(os.environ.get('REVIEW_PLAN', str(ROOT / 'artifacts/review_plan.json')))
    if plan_path.is_file():
        try:
            plan = json.loads(plan_path.read_text())
            protocol_hash = plan_hash(plan)
            manifest_path = Path(os.environ.get('SPLIT_MANIFEST', str(ROOT / 'data/splits.csv')))
            import hashlib
            if not manifest_path.is_file() or hashlib.sha256(manifest_path.read_bytes()).hexdigest() != plan['manifest_sha256']:
                raise ValueError('Frozen plan does not match the available manifest')
            if plan['split'] != os.environ.get('REVIEW_SPLIT', 'val'):
                raise ValueError('Frozen plan split does not match this review session')
            cases = plan['cases']
            if any(Path(c['file']).name != c['file'] for c in cases):
                raise ValueError('Invalid plan case filename')
            if len({c['bundle_sha256'] for c in cases}) != len(cases):
                raise ValueError('Duplicate original cases in frozen plan')
            trials = schedule(cases, session, plan.get('repeat_count', 0))
            paths = [folder / t['file'] for t in trials]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            st.error(f'Review plan unavailable or invalid: {exc}')
            st.stop()
    else:
        st.info('Exploratory review: no frozen case plan. Formal results require a versioned review plan.')
        trials = [{'file': p.name, 'trial_id': f'exploratory-{i}', 'repeat_of': None, 'cohort': 'exploratory'} for i,p in enumerate(paths)]
    selected = st.sidebar.selectbox('Case', range(len(paths)), format_func=lambda i: f'Trial {i+1:03d}')
    trial = trials[selected]
    try:
        bundle = json.loads(paths[selected].read_text())
        asset_root = folder
        if trial.get('bundle_sha256') and fingerprint(bundle) != trial['bundle_sha256']:
            raise ValueError('Saved response differs from the frozen plan')
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
        if not p.is_file():
            return None
        data = p.read_bytes()
        from PIL import Image
        with Image.open(io.BytesIO(data)) as check:
            check.verify()
        return data
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
            if reviewer_only and provenance_ok:
                original_files = verify_manifest(bundle, manifest, asset_root, verify_hashes=True, allowed_split=os.environ.get('REVIEW_SPLIT', 'val'))
                if not original_files['passed']:
                    missing = True
                    st.error('Displayed image files do not match the original manifest or are unavailable. Preference saving is disabled; the trial can be skipped.')
        except (ValueError, KeyError, OSError, TypeError):
            provenance_ok = False
    if not provenance_ok:
        st.warning('Review saving requires the agreed split manifest and matching gallery/query labels. Configure SPLIT_MANIFEST. Development defaults to validation queries.')
if reviewer_only and not mock and protocol_hash == 'exploratory':
    provenance_ok = False
    st.warning('Reviewer-only sessions require a frozen review plan. Ask the investigator to prepare it.')
blinded = True if reviewer_only else st.sidebar.toggle('Blinded comparison', value=True)
mapping = assignment(session, bundle, trial.get('trial_id', ''))
first = bundle['class_aware']
digest = fingerprint(bundle)
exposed = st.session_state.setdefault('exposed_cases', set())
if not blinded:
    exposed.add(digest)
ready = is_ready(db, session, '1.1')
with st.expander('Reviewer instructions and practice', expanded=not ready):
    st.write('Compare the same query and candidate tissue categories on both sides. Prefer references that help distinguish the categories, not simply attractive or familiar images.')
    st.write('A or B: one set is more useful. Tie: equally useful. Neither: both fail to help. Skip: you cannot judge this case. Reference labels are dataset categories, not patient diagnoses.')
    st.write('Use Demonstration for practice. Abstract fixtures are not tissue; there is no clinical answer to infer. Practice is excluded from results. Repeated cases may be included to assess consistency; no correctness feedback is provided during review.')
    acknowledged = st.checkbox('I understand the instructions and will not open investigator tools for review cases.', key='review_instructions_ack')
if not mock and not ready:
    st.warning('Complete a practice submission in Demonstration before reviewing real cases. Keep the same anonymous session ID.')
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
                    st.image(data, width=image_size)
                elif mock:
                    st.image(fixture(i+2), width=image_size)
                else:
                    st.warning('Reference unavailable')
                st.caption(f'Reference {i+1}')
with st.expander('Enlarged image inspection'):
    image_options = [('Query', first['query'])]
    for side in ['A', 'B']:
        for c in sorted(bundle[mapping[side]]['predictions'], key=lambda x:x['class_id']):
            image_options.extend((f"Set {side} - {NAMES.get(c['class_id'],c['class_id'])} - reference {i+1}", ref) for i,ref in enumerate(c['references']))
    inspect_index = st.selectbox('Image to inspect', range(len(image_options)), format_func=lambda i: image_options[i][0])
    zoom = st.slider('Inspection width', 300, 1000, 600, 50)
    inspected = image_data(image_options[inspect_index][1]['image_path'])
    if inspected:
        st.image(inspected, width=zoom)
    elif mock:
        st.image(fixture(1), width=zoom)
    st.caption('Display magnification only; no additional image detail is created. Both sides use the same reference display size.')
if blinded:
    if digest in exposed:
        st.warning('This case was already unblinded in this browser session. Use an unseen case for review.')
    form_id = hashlib.sha256((session + protocol_hash + digest + trial.get('trial_id', '')).encode()).hexdigest()[:16]
    with st.form('review_' + form_id):
        choice = st.radio('Preference', ['A', 'B', 'tie', 'neither'], index=None)
        note = st.text_area('Why? Optional. Do not enter identifying or patient information.', max_chars=2000)
        misleading = st.radio('Could either set encourage an unsupported interpretation? Exploratory feedback.', ['Not assessed','A','B','Both','Neither'], index=0)
        blocked = not provenance_ok or digest in exposed or not acknowledged or (not mock and not ready)
        submitted = st.form_submit_button('Save review', disabled=bool(missing) or blocked)
        skipped = st.form_submit_button('Skip this trial', disabled=blocked or mock)
    if submitted or skipped:
        if skipped:
            choice = "skip"
        if choice is None or not session.strip():
            st.error('Choose a preference and provide an anonymous session ID.')
        else:
            try:
                save_review(db, session, role, bundle, choice, note, mock, trial=trial, misleading=misleading, protocol_hash=protocol_hash)
                if mock:
                    mark_ready(db, session, '1.1')
                st.success('Practice completed. It is excluded from results; keep your session ID when switching to real cases.' if mock else 'Review saved. Resubmission replaces your response for this exact trial.')
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(f'Could not save review: {exc}')
if trials:
    progress = completion(trials, read_reviews(db), session, protocol_hash)
    st.write(f"Progress: {progress['completed']} completed, {progress['skipped']} skipped, {progress['unanswered']} unanswered of {progress['total']} trials.")
    st.progress((progress['completed']+progress['skipped'])/progress['total'] if progress['total'] else 0)
st.caption('References do not prove classifier reasoning or diagnosis. Blinding is a workflow aid, not a security boundary.')
