"""Investigator-only failure inspection; never use for blinded reviewers."""
import json
import os
import sys
from pathlib import Path
import streamlit as st
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.theme import apply_theme
from evaluation.case_audit import audit_case, verify_manifest
from evaluation.review import fingerprint
from evaluation.evidence_export import case_html
from evaluation.priority_cases import PRIORITY_CASES, select_queries

st.set_page_config(page_title='Failure review', layout='wide')
apply_theme()
st.title('Failure review')
st.warning('Investigator view: reveals labels and method identities. Cases opened here cannot be submitted as blinded in this browser session.')
source = st.sidebar.selectbox('Investigation source', ['Saved response pairs', 'Cached engine'])
folder = Path(os.environ.get('REVIEW_BUNDLE_DIR', str(ROOT / 'artifacts/review_bundles')))
paths = sorted(folder.glob('*.json')) if folder.is_dir() else []
rows, bundles = [], {}
if source == 'Cached engine':
    st.caption('Uses cached embeddings and classifier only. No live CONCH calls.')
    try:
        @st.cache_resource
        def get_engine():
            from src.engine import load_engine
            return load_engine()
        engine = get_engine()
        ids = select_queries(engine.df, query_ids=list(PRIORITY_CASES))
        query_id = st.selectbox('Priority validation case', ids, format_func=lambda q: f'{q} — {PRIORITY_CASES[q]}')
        pair = {m: engine.analyze_query(query_id, method=m) for m in ('class_aware', 'contrastive')}
        row = audit_case(pair)
        rows.append(row)
        bundles[query_id] = (pair, folder / 'cached.json')
    except Exception as exc:
        st.error(f'Cached investigation unavailable: {exc}')
        st.info('Run on Delta with the agreed ARTIFACT_DIR, or export the four cases using the integration guide.')
        st.stop()
elif not paths:
    st.info('No saved cases yet. Export validation pairs when cached artifacts arrive. See the review guide.')
    st.stop()
for path in paths if source == 'Saved response pairs' else []:
    try:
        pair = json.loads(path.read_text())
        row = audit_case(pair)
        rows.append(row)
        bundles[row['query_id']] = (pair, path)
    except (KeyError, ValueError, TypeError, OSError) as exc:
        st.error(f'Invalid saved case {path.name}: {exc}')
if not rows:
    st.stop()
rows.sort(key=lambda r: (list(PRIORITY_CASES).index(r['query_id']) if r['query_id'] in PRIORITY_CASES else len(PRIORITY_CASES), r['query_id']))
category = st.selectbox('Case filter', ['All', 'Priority validation cases', 'Incorrect prediction', 'Correct class outside candidates', 'Same reference sets'])
filtered = [r for r in rows if category == 'All' or
            (category == 'Priority validation cases' and r['query_id'] in PRIORITY_CASES) or
            (category == 'Incorrect prediction' and r['correct'] is False) or
            (category == 'Correct class outside candidates' and r['truth_in_candidates'] is False) or
            (category == 'Same reference sets' and r['identical_reference_sets'])]
st.caption('Descriptive diagnostics for loaded cases only. These are not unbiased cohort estimates or calibrated uncertainty measures.')
st.dataframe([{k: v for k, v in r.items() if k != 'overlap'} for r in filtered], hide_index=True)
if not filtered:
    st.info('No cases match this filter.')
    st.stop()
qid = st.selectbox('Inspect query', [r['query_id'] for r in filtered])
pair, path = bundles[qid]
st.session_state.setdefault('exposed_cases', set()).add(fingerprint(pair))
st.write(audit_case(pair))
if qid in PRIORITY_CASES:
    st.info('Handpicked investigation case: ' + PRIORITY_CASES[qid] + '. Exclude this selection from representative usefulness claims.')
if not audit_case(pair)['truth_in_candidates']:
    st.warning('The dataset label is outside the displayed candidates. References cannot repair an omitted candidate; inspect this as a classifier limitation.')
manifest = Path(os.environ.get('SPLIT_MANIFEST', str(ROOT / 'data/splits.csv')))
if manifest.is_file():
    check_hashes = st.checkbox('Verify original image hashes (may be slow)')
    checked = verify_manifest(pair, manifest, path.parent, check_hashes)
    st.write('Manifest verification', checked)
else:
    st.info('Manifest not yet available. Gallery membership and split provenance remain unverified.')

def show_image(image):
    p = Path(image['image_path'])
    p = p if p.is_absolute() else path.parent / p
    if image['image_path'] and p.is_file():
        st.image(p.read_bytes(), width=180)
    else:
        st.warning('Image unavailable')

show_image(pair['class_aware']['query'])
for column, method in zip(st.columns(2), ['class_aware', 'contrastive']):
    with column:
        st.subheader(method)
        for candidate in sorted(pair[method]['predictions'], key=lambda p: p['class_id']):
            st.write(candidate['class_id'])
            for ref in candidate['references']:
                show_image(ref)
                st.caption(ref['image_id'])

try:
    document = case_html(pair, path.parent)
    st.download_button('Download comparison evidence (HTML)', document, file_name='comparison-evidence.html', mime='text/html')
except (OSError, ValueError) as exc:
    st.warning(f'Evidence export unavailable: {exc}')
