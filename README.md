# Pathology Evidence Explorer — 2026 Ashby Hackathon

**Goal:** Compare class-aware nearest-neighbor references with contrastive reference reranking for 9-class CRC tissue classification using frozen CONCH image embeddings.

> Research / education only. Not a medical device or clinical diagnostic tool. The dataset's 9 labels are tissue classes, not 9 clinical diagnoses.

## Division of labor

**Person 1 (ML):** `scripts/make_splits.py`, `src/embedding_client.py`, `scripts/generate_embeddings.py`, `scripts/train_classifier.py`, `src/engine.py`, backend tests. Owns the shared artifact cache and produces valid `analyze_query()` outputs.

**Person 2 (UI & evaluation):** `app/streamlit_app.py`, `evaluation/compare_methods.py`, curated examples, charts, presentation. Owns evaluation checks and integration contract tests. Can develop immediately by selecting **Mock mode** in the Streamlit sidebar; `app/mock_response.json` contains fabricated scores and IDs for UI-only development.

**Together:** review split manifest, choose contrastive weights using validation only, inspect failures, run final held-out evaluation, rehearse. Don't tune on the test split.

## Install and run (inside Delta)

1. Get CONCH approval **for each teammate** (already done), and find the CONCH server's endpoint and API key in `#compute-issues`. **Never commit or share the API key.** The hosted server is accessible only from inside Delta and scheduled to stop Sunday 6 PM Central.
2. Clone/unzip this project on Delta. Use a CPU OnDemand session for heavier preprocessing/training; don't run large jobs on a login node. Python 3.10+ recommended.
3. Create an environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Set environment variables **in your shell** (do not paste real secrets into code):

   ```bash
   export DATA_ROOT=/projects/bfqi/shared/datasets/NCT-CRC-HE-100K/data-samples
   export CONCH_ENDPOINT='http://HOST_FROM_COMPUTE_ISSUES:PORT'
   export CONCH_API_KEY='KEY_FROM_COMPUTE_ISSUES'
   # Optional: put team artifacts on shared storage, but keep in mind /work/nvme is not backed up
   export ARTIFACT_DIR=/work/nvme/bfqi/teams/YOUR_TEAM/pathology-artifacts
   ```

5. Execute from the repository root:

   ```bash
   python -m scripts.make_splits
   python -m scripts.generate_embeddings --batch-size 16
   python -m scripts.train_classifier
   python -m scripts.check_contract
   python -m evaluation.compare_methods --split val
   # Freeze method parameters before final test:
   python -m evaluation.compare_methods --split test
   python -m scripts.export_demo
   streamlit run app/streamlit_app.py
   ```

   The embeddings script is resumable; rerunning skips completed rows. **Do not change the split manifest after embedding begins.** Keep a backup of artifacts and the manifest.

6. Before the hosted server closes, confirm all embeddings are cached and export the demo images. Copy the `artifacts` directory (or `ARTIFACT_DIR`) to wherever you will run Streamlit. The app uses cached vectors, the trained classifier, and saved images, and makes **no live CONCH calls**. For immediate UI development, run `streamlit run app/streamlit_app.py` and enable **Mock mode**.

## API contract

```python
from src.engine import analyze_query
result = analyze_query(
    query_id="<an actual val/test image_id from data/splits.csv>",
    method="class_aware",  # or "contrastive" / "nearest"
    top_classes=3,
    references_per_class=5,
)
```

Response: `schema_version`, `query` (`image_id`, `image_path`, `ground_truth`), `model`, `method`, `predictions` (`class_id`, `rank`, `score`, `references`), and `global_references` (populated only for `nearest`). Every reference has `image_id`, `image_path`, `class_id`, `similarity`, `discriminative_score` (null for global nearest), `ranking_score`, `rank`. Classifier `score` is `predict_proba`, **not calibrated clinical confidence**.

All images returned by `class_aware` and `contrastive` come from the gallery and match the corresponding candidate class. The global `nearest` baseline is deliberately kept separate, because its references can belong to any class.

## Data policy

- Canonical class order: ADI, BACK, DEB, LYM, MUC, MUS, NORM, STR, TUM.
- Fixed seed 42. Per class: train 200, validation 25, gallery 75, test 50. Total 3,150 images.
- SHA-256 exact duplicate filtering before assigning partitions. **Does not prevent near-duplicates or patient/slide leakage** because CRC100K lacks patient identifiers.
- Train classifier only on train; tune ranking on validation; index only gallery; evaluate once on test. Query images never appear in the gallery.
- The `data/splits.csv` is the authoritative manifest. `embedding_manifest.csv` is an exact copy, with vectors aligned by row number.
- Paths are relative to `DATA_ROOT`. To run offline, export images to `ARTIFACT_DIR/demo_images` with matching relative paths.

## Retrieval methods

- `nearest`: global top-K cosine neighbors (no class filtering).
- `class_aware`: top-K cosine neighbors **within each predicted class**.
- `contrastive`: class-aware, reranked using `0.8 * (cosine + 1)/2 + 0.2 * sigmoid(classifier_logit_margin)`. Margin is candidate-class logit minus maximum other-class logit. The weights are **engineering defaults**, not tuned or scientifically validated; change only using validation data.

General class-level morphology descriptions are stored in `config/class_attributes.json` and explicitly labeled as **not verified in the query**. No image-specific morphology attributes are inferred or localized in the MVP. This is an **example-based evidence explorer**, not a causal explanation system. A high logit margin is an optimization target, not independent proof of clinical relevance.

## Evaluation

`evaluation.compare_methods` produces `results/{val,test}_summary.json` and per-query comparison CSVs. Metrics include classification accuracy and macro-F1, average reference similarity, mean reference logit margin, and average within-reference cosine similarity (a rough diversity proxy; lower indicates more diverse embeddings). For credible clinical usefulness claims, add a small **blinded expert comparison** of reference sets, and report sample size and uncertainty.

## Quick tests

```bash
python -m pytest -q
```

Tests use synthetic vectors and do not require Delta, CONCH access, or any real pathology images.

## Constraints and references

- Hosted API: https://github.com/ncsa/ashby-hackathon-2026/blob/main/STUDENT_GUIDE.md
- Delta setup / dataset: https://github.com/ncsa/ashby-hackathon-2026/blob/main/HACKATHON_COMPUTE.md
- CONCH: https://github.com/mahmoodlab/CONCH
- Shared CRC dataset: `/projects/bfqi/shared/datasets/NCT-CRC-HE-100K/data-samples/`

**Not yet verified in this starter:** actual Delta dataset contents, hosted endpoint credentials, model response on your specific tiles, and runtime dependency compatibility on your Delta environment. Run the commands above and report any errors rather than assuming those have been tested.
