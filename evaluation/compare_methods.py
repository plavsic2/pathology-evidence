"""Held-out comparison of class-aware cosine vs contrastive reranking.

Usage: python -m evaluation.compare_methods --split val
       python -m evaluation.compare_methods --split test
"""
import argparse
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from src.engine import load_engine
from src.settings import CLASSES, artifact_dir, ROOT


def mean_pairwise_cosine(vectors):
    if len(vectors) < 2:
        return None
    gram = vectors @ vectors.T
    i, j = np.triu_indices(len(vectors), k=1)
    return float(gram[i, j].mean())


def evaluate(split):
    eng = load_engine()
    queries = eng.df.loc[eng.df.split == split, "image_id"].tolist()
    if not queries:
        raise ValueError(f"No queries in {split}")
    rows = []
    y_true, y_pred = [], []
    for qid in queries:
        base = eng.analyze_query(qid, method="class_aware")
        cont = eng.analyze_query(qid, method="contrastive")
        gt = base["query"]["ground_truth"]
        pred = base["predictions"][0]["class_id"]
        y_true.append(gt)
        y_pred.append(pred)
        for result in (base, cont):
            for candidate in result["predictions"]:
                refs = candidate["references"]
                ids = [eng.id_to_idx[r["image_id"]] for r in refs]
                rows.append({
                    "query_id": qid, "ground_truth": gt, "predicted_class": pred,
                    "candidate_class": candidate["class_id"], "method": result["method"],
                    "candidate_rank": candidate["rank"],
                    "mean_similarity": float(np.mean([r["similarity"] for r in refs])),
                    "mean_margin": float(np.mean([r["discriminative_score"] for r in refs])),
                    "mean_reference_pairwise_cosine": mean_pairwise_cosine(eng.vectors[ids]),
                    "reference_ids": "|".join(r["image_id"] for r in refs),
                })
    frame = pd.DataFrame(rows)
    summary = {
        "split": split, "n_queries": len(queries),
        "classifier_accuracy": float(accuracy_score(y_true, y_pred)),
        "classifier_macro_f1": float(f1_score(y_true, y_pred, labels=CLASSES, average="macro")),
        "confusion_matrix_class_order": CLASSES,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=CLASSES).tolist(),
        "methods": {},
        "limitations": [
            "Tile-level splits are not patient-independent; dataset lacks patient IDs.",
            "Ranking margin is optimized by the contrastive method and is not independent evidence of clinical utility.",
            "Reference similarity and diversity are embedding-based proxies, not expert diagnostic judgments."
        ]
    }
    for method, g in frame.groupby("method"):
        summary["methods"][method] = {
            "mean_similarity": float(g.mean_similarity.mean()),
            "mean_reference_margin": float(g.mean_margin.mean()),
            "mean_reference_pairwise_cosine": float(g.mean_reference_pairwise_cosine.mean()),
        }
    out = ROOT / "results"
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / f"{split}_retrieval_comparison.csv", index=False)
    (out / f"{split}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=["val", "test"], default="val")
    args = p.parse_args()
    evaluate(args.split)
