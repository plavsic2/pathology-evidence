"""Review-side protocol and persistence. Does not modify the engine contract."""
from contextlib import closing
import hashlib
import json
import math
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

METHODS = ("class_aware", "contrastive")


def fingerprint(bundle):
    return hashlib.sha256(json.dumps(bundle, sort_keys=True, allow_nan=False).encode()).hexdigest()


def validate_pair(bundle):
    """Reject incomparable displays rather than silently alter engine rankings."""
    a, b = (bundle[m] for m in METHODS)
    if a["query"] != b["query"]:
        raise ValueError("Methods must analyze the same query")
    if a["model"] != b["model"]:
        raise ValueError("Model metadata must match")
    if a.get("schema_version") != b.get("schema_version"):
        raise ValueError("Schema versions must match")
    if not a["predictions"] or len(a["predictions"]) != len(b["predictions"]):
        raise ValueError("Candidate counts must match and be nonempty")
    for result, method in ((a, METHODS[0]), (b, METHODS[1])):
        if result["method"] != method:
            raise ValueError("Method identifier does not match bundle key")
    for x, y in zip(a["predictions"], b["predictions"]):
        if (x["class_id"], x["rank"], x["score"]) != (y["class_id"], y["rank"], y["score"]):
            raise ValueError("Classifier predictions must be identical across methods")
        if not math.isfinite(x["score"]):
            raise ValueError("Nonfinite classifier score")
        if not x["references"] or len(x["references"]) != len(y["references"]):
            raise ValueError("Reference counts must match and be nonempty")
        for candidate in (x, y):
            ids = [r["image_id"] for r in candidate["references"]]
            if len(ids) != len(set(ids)) or a["query"]["image_id"] in ids:
                raise ValueError("Duplicate references or self retrieval")
            if any(r["class_id"] != candidate["class_id"] for r in candidate["references"]):
                raise ValueError("Reference class mismatch")
    return bundle


def assignment(session_id, bundle):
    seed = hashlib.sha256((session_id + fingerprint(bundle)).encode()).digest()
    methods = list(METHODS)
    random.Random(int.from_bytes(seed, "big")).shuffle(methods)
    return dict(zip(("A", "B"), methods))


def blinded_view(result):
    """Whitelist visible fields; never send scores, paths, IDs or truth to text UI."""
    return [{"class_id": p["class_id"], "reference_count": len(p["references"])}
            for p in sorted(result["predictions"], key=lambda p: p["class_id"])]


def save_review(db_path, session_id, reviewer_role, bundle, choice, note="", mock=False):
    validate_pair(bundle)
    if choice not in ("A", "B", "tie", "neither"):
        raise ValueError("Invalid review choice")
    if not session_id.strip():
        raise ValueError("Reviewer session required")
    digest = fingerprint(bundle)
    mapping = assignment(session_id, bundle)
    record = {"session_id": session_id, "reviewer_role": reviewer_role,
              "query_id": bundle[METHODS[0]]["query"]["image_id"],
              "bundle_sha256": digest, "choice": choice,
              "selected_method": mapping.get(choice, choice), "mapping": mapping,
              "note": note[:2000], "mock": bool(mock),
              "protocol_version": "1.0", "created_utc": datetime.now(timezone.utc).isoformat()}
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE IF NOT EXISTS reviews (session_id TEXT, digest TEXT, record TEXT, PRIMARY KEY(session_id,digest))")
        # Prevent double counting on Streamlit reruns; a reviewer can replace their response.
        db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?)", (session_id, digest, json.dumps(record)))
        db.commit()
    return record


def read_reviews(db_path):
    with closing(sqlite3.connect(db_path)) as db:
        return [json.loads(row[0]) for row in db.execute("SELECT record FROM reviews")]


def summarize(records):
    real = [r for r in records if not r["mock"]]
    counts = {key: sum(r["selected_method"] == key for r in real)
              for key in (*METHODS, "tie", "neither")}
    return {"n_reviews": len(real), "n_reviewers": len({r["session_id"] for r in real}),
            "n_queries": len({r["query_id"] for r in real}), "counts": counts,
            "excluded_mock_reviews": len(records) - len(real),
            "limitation": "Repeated cases and reviewers are not independent observations; preferences do not establish diagnostic benefit."}
