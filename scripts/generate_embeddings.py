"""Resumable CONCH embedding extraction; uses one shared hosted endpoint.

Usage: python -m scripts.generate_embeddings --batch-size 16
"""
import argparse
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.lib.format import open_memmap
from src.embedding_client import HostedConchClient
from src.settings import CFG, artifact_dir, manifest_path, resolve_image


def run(batch_size):
    df = pd.read_csv(manifest_path())
    out = artifact_dir()
    out.mkdir(parents=True, exist_ok=True)
    manifest_bytes = manifest_path().read_bytes()
    fingerprint = hashlib.sha256(manifest_bytes).hexdigest()
    fingerprint_path = out / "manifest.sha256"
    if fingerprint_path.exists() and fingerprint_path.read_text().strip() != fingerprint:
        raise RuntimeError("Split manifest changed since embedding began. Do not reuse cached vectors.")
    if (out / "embeddings.npy").exists() and not fingerprint_path.exists():
        raise RuntimeError("Existing cache lacks manifest fingerprint; move artifacts aside and restart.")
    fingerprint_path.write_text(fingerprint + "\n")
    df.to_csv(out / "embedding_manifest.csv", index=False)
    client = HostedConchClient()
    print("Server:", client.health(), flush=True)
    vec_path, mask_path = out / "embeddings.npy", out / "completed.npy"
    if vec_path.exists() != mask_path.exists():
        raise RuntimeError("Only one of embeddings.npy and completed.npy exists. Repair or delete both.")
    if vec_path.exists():
        vectors = np.load(vec_path, mmap_mode="r+")
        completed = np.load(mask_path)
        if vectors.shape[0] != len(df) or completed.shape != (len(df),):
            raise RuntimeError("Existing cache incompatible with manifest. Move artifacts aside and restart.")
    else:
        sample = client.embed_paths([resolve_image(df.iloc[0].relative_path)])
        vectors = open_memmap(vec_path, mode="w+", dtype="float32", shape=(len(df), sample.shape[1]))
        completed = np.zeros(len(df), dtype=bool)
        vectors[0] = sample[0]
        vectors.flush()
        completed[0] = True
        np.save(mask_path, completed)
        (out / "embedding_config.json").write_text(json.dumps({
            "encoder": "CONCH", "source": "organizer_hosted_embed",
            "embedding_version": CFG["embedding_version"],
            "dimension": int(sample.shape[1]), "l2_normalized": True,
            "manifest": "embedding_manifest.csv"
        }, indent=2))
    todo = np.flatnonzero(~completed)
    for start in range(0, len(todo), batch_size):
        idx = todo[start:start + batch_size]
        paths = [resolve_image(df.iloc[int(i)].relative_path) for i in idx]
        missing = [str(p) for p in paths if not p.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing input files: {missing[:3]}")
        vectors[idx] = client.embed_paths(paths)
        vectors.flush()
        completed[idx] = True
        np.save(mask_path, completed)
        print(f"Embedded {int(completed.sum())}/{len(df)}", flush=True)
    print("Done:", vec_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    run(args.batch_size)
