"""Shared configuration, labels, and artifact paths."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(Path(path).read_text())


CLASSES = load_json(ROOT / "config/classes.json")["classes"]
NAMES = load_json(ROOT / "config/classes.json")["names"]
CFG = load_json(ROOT / "config/experiment.json")


def data_root():
    return Path(os.environ.get("DATA_ROOT", "/projects/bfqi/shared/datasets/NCT-CRC-HE-100K/data-samples")).expanduser()


def artifact_dir():
    p = Path(os.environ.get("ARTIFACT_DIR", str(ROOT / "artifacts"))).expanduser()
    if not p.is_absolute():
        p = ROOT / p
    return p


def manifest_path():
    return ROOT / "data/splits.csv"


def resolve_image(relative_path):
    path = data_root() / relative_path
    if path.exists():
        return path
    # Supports a portable demo with only copied images.
    fallback = artifact_dir() / "demo_images" / relative_path
    return fallback
