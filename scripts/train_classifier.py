"""Train classifier on train partition; report validation only."""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from src.settings import CFG, CLASSES, artifact_dir


def main():
    out = artifact_dir()
    df = pd.read_csv(out / "embedding_manifest.csv")
    done = np.load(out / "completed.npy")
    if not done.all():
        raise RuntimeError("Not all embeddings are complete")
    X = np.load(out / "embeddings.npy")
    train = df.split.to_numpy() == "train"
    val = df.split.to_numpy() == "val"
    clf = LogisticRegression(C=CFG["classifier_C"], max_iter=CFG["classifier_max_iter"], random_state=CFG["seed"])
    clf.fit(X[train], df.label.to_numpy()[train])
    if list(clf.classes_) != CLASSES:
        raise ValueError("Class order mismatch")
    pred = clf.predict(X[val])
    metrics = {"validation_accuracy": float(accuracy_score(df.label[val], pred)),
               "validation_macro_f1": float(f1_score(df.label[val], pred, labels=CLASSES, average="macro")),
               "train_count": int(train.sum()), "validation_count": int(val.sum())}
    joblib.dump(clf, out / "classifier.joblib")
    (out / "validation_classifier_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
