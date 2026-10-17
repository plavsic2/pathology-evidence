"""Copy gallery and test/val tiles for a portable CPU-only demo.

Usage: python -m scripts.export_demo
"""
import shutil
import pandas as pd
from src.settings import artifact_dir, data_root


def main():
    df = pd.read_csv(artifact_dir() / "embedding_manifest.csv")
    target = artifact_dir() / "demo_images"
    count = 0
    for row in df.itertuples():
        if row.split not in ("gallery", "val", "test"):
            continue
        src = data_root() / row.relative_path
        dst = target / row.relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
            count += 1
    print(f"Copied {count} tiles to {target}; not committed to Git")


if __name__ == "__main__":
    main()
