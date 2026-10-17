"""Stable JSON-serializable retrieval contract; no live inference required."""
import json
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from src.settings import CFG, CLASSES, artifact_dir, resolve_image


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40, 40)))


class EvidenceEngine:
    def __init__(self, manifest, vectors, classifier, *, alpha=0.8, beta=0.2):
        self.df = manifest.reset_index(drop=True)
        self.vectors = np.asarray(vectors, dtype=np.float32)
        self.clf = classifier
        self.alpha, self.beta = float(alpha), float(beta)
        if self.vectors.ndim != 2 or len(self.df) != len(self.vectors):
            raise ValueError("Manifest/embedding shape mismatch")
        if self.df.image_id.duplicated().any():
            raise ValueError("Duplicate image IDs")
        if not np.allclose(np.linalg.norm(self.vectors, axis=1), 1, atol=1e-3):
            raise ValueError("Expected L2-normalized embeddings")
        self.id_to_idx = {str(x): i for i, x in enumerate(self.df.image_id)}
        self.gallery_idx = np.flatnonzero(self.df.split.to_numpy() == "gallery")
        if not len(self.gallery_idx):
            raise ValueError("Empty gallery")
        self.class_to_gallery = {
            c: self.gallery_idx[self.df.iloc[self.gallery_idx].label.to_numpy() == c]
            for c in CLASSES
        }
        if any(len(x) == 0 for x in self.class_to_gallery.values()):
            raise ValueError("At least one class has an empty gallery")
        self.classifier_classes = list(self.clf.classes_)
        if set(self.classifier_classes) != set(CLASSES):
            raise ValueError("Classifier class set does not match canonical classes")

    def _refs(self, qvec, candidates, class_id, method, count):
        if not len(candidates):
            return []
        rvecs = self.vectors[candidates]
        cos = np.clip(rvecs @ qvec, -1.0, 1.0)
        logits = np.asarray(self.clf.decision_function(rvecs))
        cpos = self.classifier_classes.index(class_id)
        own = logits[:, cpos]
        other = np.max(np.delete(logits, cpos, axis=1), axis=1)
        margins = own - other
        # Bounded, explicit scoring: (cos+1)/2 and sigmoid(margin).
        scores = ((self.alpha * (cos + 1) / 2 + self.beta * sigmoid(margins))
                  if method == "contrastive" else cos)
        order = np.argsort(-scores, kind="stable")[:count]
        output = []
        for rank, j in enumerate(order, 1):
            idx = int(candidates[j])
            row = self.df.iloc[idx]
            output.append({
                "image_id": str(row.image_id),
                "image_path": str(resolve_image(row.relative_path)),
                "class_id": str(row.label),
                "similarity": float(cos[j]),
                "discriminative_score": float(margins[j]),
                "ranking_score": float(scores[j]),
                "rank": rank,
            })
        return output

    def analyze_query(self, query_id, method="class_aware", top_classes=3, references_per_class=5):
        if method not in ("nearest", "class_aware", "contrastive"):
            raise ValueError("method must be nearest, class_aware, or contrastive")
        if not (1 <= top_classes <= len(CLASSES) and 1 <= references_per_class <= 75):
            raise ValueError("Invalid top_classes or references_per_class")
        idx = self.id_to_idx.get(str(query_id))
        if idx is None:
            raise KeyError(f"Unknown query_id {query_id}")
        row = self.df.iloc[idx]
        if row.split not in ("val", "test"):
            raise ValueError("Queries must be from validation or test partition")
        qvec = self.vectors[idx]
        probabilities = self.clf.predict_proba(qvec[None, :])[0]
        order = np.argsort(-probabilities, kind="stable")[:top_classes]
        preds = []
        for rank, pos in enumerate(order, 1):
            cls = str(self.classifier_classes[pos])
            candidates = self.class_to_gallery[cls]
            refs = [] if method == "nearest" else self._refs(qvec, candidates, cls, method, references_per_class)
            preds.append({"class_id": cls, "rank": rank, "score": float(probabilities[pos]), "references": refs})
        global_refs = []
        if method == "nearest":
            # Global nearest-neighbor results, not mislabeled as class-specific evidence.
            cos = self.vectors[self.gallery_idx] @ qvec
            chosen = self.gallery_idx[np.argsort(-cos, kind="stable")[:references_per_class]]
            for rank, ridx in enumerate(chosen, 1):
                rr = self.df.iloc[int(ridx)]
                global_refs.append({"image_id": str(rr.image_id), "image_path": str(resolve_image(rr.relative_path)),
                                    "class_id": str(rr.label), "similarity": float(cos[np.where(self.gallery_idx == ridx)[0][0]]),
                                    "discriminative_score": None, "ranking_score": float(cos[np.where(self.gallery_idx == ridx)[0][0]]), "rank": rank})
        return {
            "schema_version": "1.0",
            "query": {"image_id": str(row.image_id), "image_path": str(resolve_image(row.relative_path)),
                      "ground_truth": str(row.label)},
            "model": {"encoder": "CONCH", "classifier": "logistic_regression",
                      "embedding_version": CFG["embedding_version"]},
            "method": method,
            "predictions": preds,
            "global_references": global_refs,
        }


@lru_cache(maxsize=1)
def load_engine():
    out = artifact_dir()
    manifest = pd.read_csv(out / "embedding_manifest.csv")
    completed = np.load(out / "completed.npy")
    if not completed.all():
        raise RuntimeError("Embedding extraction incomplete")
    vectors = np.load(out / "embeddings.npy")
    classifier = joblib.load(out / "classifier.joblib")
    return EvidenceEngine(manifest, vectors, classifier,
                          alpha=CFG["contrastive_alpha"], beta=CFG["contrastive_beta"])


def analyze_query(query_id, method="class_aware", top_classes=3, references_per_class=5):
    return load_engine().analyze_query(query_id, method, top_classes, references_per_class)
