import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from src.engine import EvidenceEngine
from src.settings import CLASSES


def synthetic_engine():
    rng = np.random.default_rng(42)
    rows, X = [], []
    for k, label in enumerate(CLASSES):
        for split, n in (("train", 6), ("val", 2), ("gallery", 5), ("test", 2)):
            for j in range(n):
                vec = rng.normal(scale=0.1, size=18)
                vec[k] += 2
                vec /= np.linalg.norm(vec)
                X.append(vec)
                rows.append({"image_id": f"{label}_{split}_{j}", "relative_path": f"{label}/fake_{j}.tif",
                             "label": label, "split": split, "sha256": f"{label}_{split}_{j}"})
    df = pd.DataFrame(rows)
    X = np.asarray(X, dtype=np.float32)
    train = df.split == "train"
    clf = LogisticRegression(max_iter=1000).fit(X[train], df.label[train])
    return EvidenceEngine(df, X, clf)


def test_contract_and_no_leakage():
    eng = synthetic_engine()
    for method in ("nearest", "class_aware", "contrastive"):
        out = eng.analyze_query("TUM_test_0", method, references_per_class=3)
        assert out["schema_version"] == "1.0"
        assert len(out["predictions"]) == 3
        refs = out["global_references"] if method == "nearest" else [r for p in out["predictions"] for r in p["references"]]
        assert len(refs) == (3 if method == "nearest" else 9)
        assert all("gallery" in r["image_id"] for r in refs)
        assert all(r["image_id"] != "TUM_test_0" for r in refs)
        if method != "nearest":
            assert all(r["class_id"] == p["class_id"] for p in out["predictions"] for r in p["references"])


def test_reject_training_queries():
    with pytest.raises(ValueError):
        synthetic_engine().analyze_query("TUM_train_0")


def test_invalid_method():
    with pytest.raises(ValueError):
        synthetic_engine().analyze_query("TUM_val_0", method="other")
