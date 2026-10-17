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


def assignment(session_id, bundle, trial_id=""):
    seed = hashlib.sha256((session_id + trial_id + fingerprint(bundle)).encode()).digest()
    methods = list(METHODS)
    random.Random(int.from_bytes(seed, "big")).shuffle(methods)
    return dict(zip(("A", "B"), methods))


def blinded_view(result):
    """Whitelist visible fields; never send scores, paths, IDs or truth to text UI."""
    return [{"class_id": p["class_id"], "reference_count": len(p["references"])}
            for p in sorted(result["predictions"], key=lambda p: p["class_id"])]


def save_review(db_path, session_id, reviewer_role, bundle, choice, note="", mock=False, *, trial=None, misleading="Not assessed", protocol_hash="exploratory"):
    validate_pair(bundle)
    if choice not in ("A", "B", "tie", "neither", "skip"):
        raise ValueError("Invalid review choice")
    if not session_id.strip():
        raise ValueError("Reviewer session required")
    digest = fingerprint(bundle)
    trial = trial or {}
    trial_id = trial.get("trial_id", "")
    mapping = assignment(session_id, bundle, trial_id)
    record = {"session_id": session_id, "reviewer_role": reviewer_role,
              "query_id": bundle[METHODS[0]]["query"]["image_id"],
              "bundle_sha256": digest, "choice": choice,
              "selected_method": mapping.get(choice, choice), "mapping": mapping,
              "note": note[:2000], "mock": bool(mock),
              "protocol_version": "1.1", "protocol_hash": protocol_hash, "trial_id": trial_id,
              "repeat_of": trial.get("repeat_of"), "cohort": trial.get("cohort", "exploratory"),
              "misleading": misleading, "misleading_method": mapping.get(misleading, misleading), "created_utc": datetime.now(timezone.utc).isoformat()}
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE IF NOT EXISTS reviews (session_id TEXT, digest TEXT, record TEXT, PRIMARY KEY(session_id,digest))")
        # Prevent double counting on Streamlit reruns; a reviewer can replace their response.
        db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?)", (session_id, digest + ":" + protocol_hash + ":" + trial_id, json.dumps(record)))
        db.commit()
    return record


def read_reviews(db_path):
    if not Path(db_path).is_file():
        return []
    with closing(sqlite3.connect(db_path)) as db:
        exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'").fetchone()
        return [json.loads(row[0]) for row in db.execute("SELECT record FROM reviews")] if exists else []


def summarize(records):
    eligible = [r for r in records if not r['mock'] and not r.get('repeat_of')]
    real = [r for r in eligible if r['choice'] != 'skip']
    counts = {key: sum(r['selected_method'] == key for r in real)
              for key in (*METHODS, 'tie', 'neither')}
    by_key = {(r['session_id'], r.get('protocol_hash'), r.get('trial_id')): r for r in records if not r['mock']}
    consistency = []
    for r in records:
        if r['mock'] or not r.get('repeat_of') or r['choice'] == 'skip':
            continue
        original = by_key.get((r['session_id'], r.get('protocol_hash'), r['repeat_of']))
        if original and original['choice'] != 'skip':
            consistency.append(original['selected_method'] == r['selected_method'])
    primary = [r for r in real if r.get('cohort') == 'random']
    return {'n_reviews': len(real), 'n_reviewers': len({r['session_id'] for r in real}),
            'n_queries': len({r['query_id'] for r in real}), 'counts': counts,
            'primary_random_counts': {key: sum(r['selected_method'] == key for r in primary) for key in counts},
            'skipped_original_trials': sum(r['choice'] == 'skip' for r in eligible),
            'repeat_pairs_compared': len(consistency), 'repeat_pairs_agree': sum(consistency),
            'misleading_counts': {key: sum(r.get('misleading_method', 'Not assessed') == key for r in real) for key in [*METHODS, 'Both', 'Neither', 'Not assessed']},
            'excluded_mock_reviews': sum(r['mock'] for r in records),
            'protocols': sorted({r.get('protocol_hash', 'legacy') for r in real}),
            'limitation': 'Repeated cases and reviewers are not independent observations; preferences do not establish diagnostic benefit. Main counts exclude repeat trials and skips. Separate protocols must be reported separately.'}


def mark_ready(db_path, session_id, protocol_hash):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS onboarding (session_id TEXT, protocol_hash TEXT, PRIMARY KEY(session_id, protocol_hash))')
        db.execute('INSERT OR IGNORE INTO onboarding VALUES (?,?)', (session_id, protocol_hash))
        db.commit()


def is_ready(db_path, session_id, protocol_hash):
    if not Path(db_path).is_file():
        return False
    with closing(sqlite3.connect(db_path)) as db:
        if not db.execute("SELECT name FROM sqlite_master WHERE name='onboarding'").fetchone():
            return False
        return db.execute('SELECT 1 FROM onboarding WHERE session_id=? AND protocol_hash=?', (session_id, protocol_hash)).fetchone() is not None
