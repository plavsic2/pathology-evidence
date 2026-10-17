"""Smoke test end-to-end JSON contract and split invariants."""
import json
import pandas as pd
from src.engine import load_engine
from src.settings import artifact_dir


def main():
    eng = load_engine()
    df = eng.df
    assert df.image_id.is_unique
    assert df.sha256.is_unique
    assert set(df.split) == {"train", "val", "gallery", "test"}
    qid = str(df.loc[df.split == "val", "image_id"].iloc[0])
    gallery_ids = set(df.loc[df.split == "gallery", "image_id"])
    for method in ("nearest", "class_aware", "contrastive"):
        result = eng.analyze_query(qid, method)
        assert result["schema_version"] == "1.0"
        assert len(result["predictions"]) == 3
        refs = result["global_references"] if method == "nearest" else [r for p in result["predictions"] for r in p["references"]]
        assert len(refs) == (5 if method == "nearest" else 15)
        assert all(r["image_id"] in gallery_ids for r in refs)
        assert all(r["image_id"] != qid for r in refs)
        json.dumps(result, allow_nan=False)
        print(f"{method}: PASS")
    print("All integration checks passed")


if __name__ == "__main__":
    main()
