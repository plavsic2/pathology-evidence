"""Interactive evidence exploration, separate from frozen reference review."""
import copy
import io
import json
import os
import re
import sys
from pathlib import Path
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.theme import apply_theme
from evaluation.review import fingerprint

NAMES = json.loads((ROOT / 'config/classes.json').read_text())['names']
st.set_page_config(page_title='Visual Evidence Explorer', layout='wide', initial_sidebar_state='auto')
apply_theme()
st.title('Visual Evidence Explorer')
st.caption('Research and education only. Not for clinical diagnosis or treatment decisions.')
st.info('Compare the query with examples of three candidate tissue types. Generated observations may be incomplete or incorrect; verify them against the images.')
query_panel = st.sidebar.container()
source = st.sidebar.selectbox('Image source', ['Saved validation cases', 'Cached backend'])
st.sidebar.caption('Query source: select an existing validation image. This prototype does not upload or analyze arbitrary new images.')
asset_root = ROOT
pair = None
if source == 'Saved validation cases':
    folder = Path(os.environ.get('EVIDENCE_BUNDLE_DIR', str(ROOT / 'artifacts/priority_validation')))
    paths = sorted(folder.glob('case_*.json'))
    if not paths:
        st.info('No saved cases available. Configure EVIDENCE_BUNDLE_DIR or use the cached backend on Delta.')
        st.stop()
    selected = st.sidebar.selectbox('Example', range(len(paths)), format_func=lambda i: f'Example {i+1}')
    try:
        pair = json.loads(paths[selected].read_text())
        analysis = copy.deepcopy(pair['contrastive'])
        asset_root = folder
    except (OSError, ValueError, KeyError):
        st.error('This saved case could not be loaded.')
        st.stop()
else:
    try:
        @st.cache_resource
        def engine():
            from src.engine import load_engine
            return load_engine()
        backend = engine()
        ids = sorted(backend.df.loc[backend.df.split == 'val', 'image_id'].astype(str))
        selected = st.sidebar.selectbox('Example', range(len(ids)), format_func=lambda i: f'Example {i+1}')
        analysis = backend.analyze_query(ids[selected], method='contrastive', top_classes=3, references_per_class=3)
    except Exception:
        st.error('Cached images and analysis are unavailable. Check the artifact and dataset paths on the host.')
        st.stop()

# Use the same image order as the backend's A(query), B/C/D(reference) prompt.
analysis['predictions'] = analysis['predictions'][:3]
for prediction in analysis['predictions']:
    prediction['references'] = prediction['references'][:3]
for item in [analysis['query']] + [r for p in analysis['predictions'] for r in p['references']]:
    path = Path(item['image_path'])
    item['image_path'] = str(path if path.is_absolute() else asset_root / path)
if pair is not None:
    st.session_state.setdefault('exposed_cases', set()).add(fingerprint(pair))
digest = fingerprint(analysis)

def picture(item, width):
    try:
        data = Path(item['image_path']).read_bytes()
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
        st.image(data, width=width)
        return True
    except (OSError, ValueError):
        st.warning('Image unavailable')
        return False

with query_panel:
    st.subheader('Query - Image A')
    picture(analysis['query'], 160)
    st.caption('Kept here while you scroll the comparison. A is always the query; B, C and D are references within each candidate group.')

@st.dialog('Compare enlarged images', width='large')
def inspect_reference(reference, label):
    for col, title, item in zip(st.columns(2), ['Query - Image A', label], [analysis['query'], reference]):
        with col:
            st.markdown('**' + title + '**')
            picture(item, 350)
    st.caption('Display enlargement only. A 224 x 224 tile becomes softer when enlarged; no additional underlying detail is created.')

def observation_bullet(text):
    # Keep generated wording, but make image pointers readable and prevent
    # model text from introducing HTML, links, or arbitrary Markdown.
    def escape(chunk):
        return re.sub(r'([\\`*_{}\[\]()#+.!|<>-])', r'\\\1', chunk)
    pieces, offset = [], 0
    for match in re.finditer(r'\b(?:Image\s+)?([ABCD])\b', text):
        pieces.append(escape(text[offset:match.start()]))
        letter = match.group(1)
        pieces.append('**' + ('Query (A)' if letter == 'A' else 'Reference ' + letter) + '**')
        offset = match.end()
    pieces.append(escape(text[offset:]))
    return '- ' + ''.join(pieces)

st.markdown('''<style>
@media (max-width: 900px) {
  div:has(> .st-key-query_pin) { position: sticky; top: 2.8rem; z-index: 99;
    background: #101010; padding: 8px; border: 1px solid #343434; border-radius: 8px; }
}
</style>''', unsafe_allow_html=True)
with st.container(key='query_pin'):
    image_col, label_col = st.columns([1, 2])
    with image_col:
        picture(analysis['query'], 100)
    with label_col:
        st.markdown('**Query - Image A**')
        st.caption('Compare references B, C and D with A.')
st.caption('Candidate categories are suggestions, not confirmed diagnoses. Their scores and the dataset answer are hidden in this view.')
key_available = bool(os.environ.get('LUMEN_API_KEY', '').strip())
if not key_available:
    st.caption('Visual observations are unavailable until the host is configured. Reference images remain available.')
generated = st.session_state.setdefault('visual_observations', {})
saved_path = Path(os.environ.get('EVIDENCE_SNAPSHOT_DIR', str(ROOT / 'artifacts/evidence_observations'))) / (digest + '.json')
if digest not in generated and saved_path.is_file():
    try:
        snapshot = json.loads(saved_path.read_text())
        if snapshot['analysis_sha256'] == digest:
            generated[digest] = snapshot['result']
            st.session_state.setdefault('offline_observation_digests', set()).add(digest)
    except (OSError, ValueError, KeyError, TypeError):
        pass
if digest in st.session_state.get('offline_observation_digests', set()):
    st.caption('Previously generated observations - local saved copy; not independently validated.')
if st.button('Generate visual observations', disabled=not key_available):
    try:
        from src.evidence_explainer import explain_candidates
        with st.spinner('Comparing visible features in the images...'):
            result = explain_candidates(analysis, max_refs=3)
        generated[digest] = result
    except Exception:
        # Do not expose response bodies, endpoint details, credentials or traces.
        generated[digest] = {'candidates': []}
        st.warning('Visual explanation temporarily unavailable')
result = generated.get(digest, {'candidates': []})
if result.get('candidates') and st.button('Save observations for offline replay'):
    saved_path.parent.mkdir(parents=True, exist_ok=True)
    saved_path.write_text(json.dumps({'analysis_sha256': digest, 'result': result}, indent=2))
    st.success('Saved on this computer for this exact query and reference set. No API key is included.')
observations = {c['class_id']: c for c in result.get('candidates', [])}

st.subheader('Candidate tissue types')
for col, prediction in zip(st.columns(3), analysis['predictions']):
    with col:
        cid = prediction['class_id']
        st.subheader(NAMES.get(cid, cid))
        for i, ref in enumerate(prediction['references']):
            picture(ref, 180)
            st.caption('Image ' + chr(ord('B') + i) + ' - reference ' + str(i+1))
            label = 'Image ' + chr(ord('B') + i)
            if st.button('Enlarge ' + label, key='inspect_' + digest + cid + str(i)):
                inspect_reference(ref, NAMES.get(cid, cid) + ' - ' + label)
        candidate = observations.get(cid)
        if candidate is None or candidate.get('explanation_unavailable', False):
            st.warning('Visual explanation temporarily unavailable')
        else:
            st.markdown('**Supporting visual similarities**')
            supporting = candidate.get('supporting', [])
            if not supporting:
                st.write('No specific supporting similarities reported.')
            for observation in supporting:
                st.markdown(observation_bullet(observation))
            st.markdown('**Contrasting visual differences**')
            contrasting = candidate.get('contrasting', [])
            if not contrasting:
                st.write('No specific contrasting differences reported.')
            for observation in contrasting:
                st.markdown(observation_bullet(observation))
        st.caption('Observations compare the query with this reference group. They do not establish the tissue category or explain the classifier\'s internal reasoning.')

with st.expander('Enlarge an image'):
    options = [('Query image', analysis['query'])]
    for prediction in analysis['predictions']:
        options.extend((NAMES.get(prediction['class_id'], prediction['class_id']) + ' - Image ' + chr(ord('B')+i), ref) for i, ref in enumerate(prediction['references']))
    choice = st.selectbox('Image to enlarge', range(len(options)), format_func=lambda i: options[i][0])
    width = st.slider('Display width', 300, 1000, 600, 50)
    picture(options[choice][1], width)
    st.caption('Display enlargement only; no additional tissue detail is inferred.')
st.caption('Exploration view: keep separate from blinded reference-only evaluation. No review preferences are collected here.')
