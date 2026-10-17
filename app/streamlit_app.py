"""Offline-capable Streamlit evidence browser.

Run: streamlit run app/streamlit_app.py
"""
import json
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine import load_engine
from src.settings import NAMES, CLASSES, ROOT

st.set_page_config(page_title="Pathology Evidence Explorer", layout="wide")
st.title("Pathology Evidence Explorer")
st.caption("Research prototype · CONCH frozen embeddings · CRC tissue categories, not clinical diagnoses")

@st.cache_resource
def get_engine():
    return load_engine()

mock_mode = st.sidebar.checkbox("Mock mode (UI development)", value=False)
if mock_mode:
    engine = None
    result = json.loads((Path(__file__).parent / "mock_response.json").read_text())
    st.info("MOCK MODE: all labels and scores are fabricated for interface development.")
else:
    try:
        engine = get_engine()
    except Exception as exc:
        st.error(f"Artifacts unavailable: {exc}")
        st.info("Enable 'Mock mode' in the sidebar or run the data pipeline. See README.md.")
        st.stop()
    split = st.sidebar.radio("Query partition", ["val", "test"], index=0)
    subset = engine.df.loc[engine.df.split == split]
    query_id = st.sidebar.selectbox("Query image ID", subset.image_id.tolist(), format_func=lambda x: f"{x} ({subset.set_index('image_id').loc[x, 'label']})")
    method = st.sidebar.radio("Retrieval method", ["class_aware", "contrastive", "nearest"], index=0)
    result = engine.analyze_query(query_id, method=method)
method = result["method"]
show_truth = st.sidebar.checkbox("Show dataset ground truth", value=False)
show_details = st.sidebar.checkbox("Show ranking metrics", value=True)

left, right = st.columns([1, 2])
with left:
    st.subheader("Query tile")
    qpath = Path(result["query"]["image_path"])
    if result["query"]["image_path"] and qpath.is_file():
        st.image(str(qpath), use_container_width=True)
    else:
        st.warning("Image file unavailable. Run export_demo on Delta and copy demo_images.")
    st.code(result["query"]["image_id"])
    if show_truth:
        st.write("Ground truth:", result["query"]["ground_truth"])
with right:
    st.subheader("Candidate tissue classes")
    for p in result["predictions"]:
        st.write(f"**{p['rank']}. {p['class_id']} — {NAMES[p['class_id']]}** · classifier score {p['score']:.3f}")
    st.caption("Scores are classifier outputs, not clinically calibrated probabilities.")

if method == "nearest":
    st.subheader("Global nearest neighbors (not class-filtered)")
    refs = result["global_references"]
    cols = st.columns(len(refs))
    for col, r in zip(cols, refs):
        with col:
            if r["image_path"] and Path(r["image_path"]).is_file():
                st.image(r["image_path"], use_container_width=True)
            st.caption(f"{r['class_id']} · sim {r['similarity']:.3f}")
else:
    st.subheader("Reference evidence by candidate class")
    attributes = json.loads((ROOT / "config/class_attributes.json").read_text())["attributes"]
    for p in result["predictions"]:
        with st.expander(f"{p['class_id']} — {NAMES[p['class_id']]} (rank {p['rank']})", expanded=(p['rank'] <= 2)):
            st.caption("General class morphology (not verified in this query): " + attributes[p["class_id"]])
            cols = st.columns(len(p["references"]))
            for col, r in zip(cols, p["references"]):
                with col:
                    if r["image_path"] and Path(r["image_path"]).is_file():
                        st.image(r["image_path"], use_container_width=True)
                    else:
                        st.warning("Image missing")
                    st.caption(f"{r['image_id']} · sim {r['similarity']:.3f}")
                    if show_details:
                        st.caption(f"margin {r['discriminative_score']:.2f} · rank score {r['ranking_score']:.3f}")

st.divider()
st.caption("Retrieved references are labeled dataset examples, not independently verified diagnostic explanations. Similarity does not prove morphological or causal support.")
with st.expander("Analysis JSON"):
    st.json(result)
