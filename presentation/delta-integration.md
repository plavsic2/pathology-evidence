# Delta integration: four priority validation cases

Agreed shared cache: `/work/nvme/bfqi/teams/team58/pathology-artifacts`.
The integrated Person 2 branch incorporates Person 1 commit `a08ccc6ccac0cb883e9dc5f796411575ed9182bc`, including the original split manifest unchanged. Do not regenerate splits or embeddings.

## Run on Delta

From a checkout of `person2/blinded-review`, activate the team's Python environment with the requirements installed. These commands read the cache; no CONCH key or new embedding job is required.

```bash
export ARTIFACT_DIR=/work/nvme/bfqi/teams/team58/pathology-artifacts
export DATA_ROOT=/projects/bfqi/shared/datasets/NCT-CRC-HE-100K/data-samples
export SPLIT_MANIFEST="$PWD/data/splits.csv"
python -m scripts.check_contract
streamlit run app/streamlit_app.py --server.address 127.0.0.1
```

Use **Failure review → Investigation source → Cached engine**. Select a priority validation case to see named class-aware and contrastive columns, the same query, alphabetical class panels, and the candidate omission warning. This is an unblinded investigator workflow; do not submit these viewed cases as blinded judgments.

For a portable review without model dependencies, export original images and paired JSON to a new empty directory:

```bash
python -m evaluation.prepare_review --priority-cases --output artifacts/priority_validation
export REVIEW_BUNDLE_DIR="$PWD/artifacts/priority_validation"
streamlit run app/streamlit_app.py --server.address 127.0.0.1
```

Choose **Failure review → Saved response pairs → Priority validation cases**. Copy the entire export folder intact to another machine if needed; JSON paths are relative and original images preserve manifest hashes. Keep this targeted folder separate from the random evaluation bundle and frozen review plan. The export command refuses to overwrite an existing nonempty folder.

## What to inspect

| Validation query | Partner's observation | Inspection question |
|---|---|---|
| `70eccc3f2e78b00d` | TUM vs NORM, nearly tied | Do the two reference sets make the competing classes easier to distinguish? |
| `94394b287ecddee1` | STR predicted as MUS | Does reranking clarify the incorrect prediction or reinforce it? |
| `11a3e8d3096d83e8` | MUC predicted as TUM, score 0.858 | Is MUC even among the displayed candidates? A missing class cannot be recovered by reference reranking. |
| `b1d78ff6551a8c8c` | MUS predicted as STR, DEB close | Are references useful across all three competing categories? |

The committed table contains 215 correct of 225 validation examples (95.56%). This verifies the table's arithmetic, not a local rerun of the classifier. Accuracy does not establish reference usefulness. Record unchanged references, misleading examples, and failed cases as well as helpful ones. Model scores are not calibrated clinical probabilities.

## Integration status

Backend API and JSON schema unchanged. Manifest unchanged. Real Delta cache loading and image inspection still require execution on Delta or a portable export: this workstation has neither the cache nor the tissue images. No real reference-quality conclusions have been made here. Person 1 continues to own retrieval metrics and cache changes.
