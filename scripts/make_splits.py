"""Deterministic balanced CRC sample, deduplicated by SHA-256 before splitting.

Usage: python -m scripts.make_splits
"""
import hashlib
import random
from pathlib import Path
import pandas as pd
from src.settings import CLASSES, CFG, data_root, manifest_path

EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root, output, counts, seed):
    rng = random.Random(seed)
    seen_hashes = set()
    rows = []
    for label in CLASSES:
        folder = Path(root) / label
        if not folder.is_dir():
            raise FileNotFoundError(f"Expected class folder missing: {folder}")
        candidates = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
        rng.shuffle(candidates)
        needed = sum(counts.values())
        chosen = []
        for path in candidates:
            digest = file_sha256(path)
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            chosen.append((path, digest))
            if len(chosen) == needed:
                break
        if len(chosen) != needed:
            raise ValueError(f"{label}: need {needed} unique images; found {len(chosen)}. Reduce counts in config/experiment.json.")
        pos = 0
        for split in ("train", "val", "gallery", "test"):
            for path, digest in chosen[pos:pos + counts[split]]:
                rel = path.relative_to(root).as_posix()
                image_id = hashlib.sha1(rel.encode()).hexdigest()[:16]
                rows.append({"image_id": image_id, "relative_path": rel, "label": label, "split": split, "sha256": digest})
            pos += counts[split]
    df = pd.DataFrame(rows).sort_values(["split", "label", "image_id"]).reset_index(drop=True)
    assert df.image_id.is_unique and df.sha256.is_unique
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Wrote {len(df)} rows to {output}\n{pd.crosstab(df.label, df.split)}")
    return df


if __name__ == "__main__":
    build_manifest(data_root(), manifest_path(), CFG["counts_per_class"], CFG["seed"])
