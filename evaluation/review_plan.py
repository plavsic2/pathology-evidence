"""Freeze a review-side sampling plan without changing the dataset manifest."""
import argparse
import hashlib
import json
import random
from pathlib import Path
from evaluation.case_audit import audit_case, verify_manifest
from evaluation.review import fingerprint

PROTOCOL_VERSION = '1.1'


def plan_hash(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()


def freeze_plan(folder, manifest, count=30, seed=42, split='val'):
    cases = []
    for p in sorted(Path(folder).glob('case_*.json')):
        bundle = json.loads(p.read_text())
        checked = verify_manifest(bundle, manifest, p.parent, allowed_split=split)
        if not checked['passed']:
            raise ValueError(f'{p.name}: manifest verification failed: {checked["errors"]}')
        cases.append((p, bundle, audit_case(bundle)))
    if not cases or count < 1:
        raise ValueError('Need at least one valid case and a positive count')
    if len({fingerprint(b) for _, b, _ in cases}) != len(cases):
        raise ValueError('Duplicate response pairs in sampling pool')
    rng = random.Random(seed)
    rng.shuffle(cases)
    n = min(count, len(cases))
    random_count = max(1, (2 * n + 2) // 3)
    selected = [(x, 'random') for x in cases[:random_count]]
    remaining = sorted(cases[random_count:], key=lambda x: (x[2]['top_score_gap'] if x[2]['top_score_gap'] is not None else 1, x[2]['query_id']))
    selected += [(x, 'difficult') for x in remaining[:n-random_count]]
    return {'protocol_version': PROTOCOL_VERSION, 'seed': seed, 'split': split,
            'manifest_sha256': hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
            'pool_size': len(cases), 'requested_count': count,
            'selection': 'Two thirds seeded random; remaining lowest classifier top-score gaps among unselected cases. Difficult cohort is secondary.',
            'repeat_count': min(2, n // 4),
            'cases': [{'file': p.name, 'bundle_sha256': fingerprint(b), 'cohort': cohort}
                      for ((p, b, _), cohort) in selected]}


def schedule(cases, session_id, repeat_count=2):
    """Return anonymous trial IDs; repeats are separated by >=3 other trials."""
    ordered = list(cases)
    seed = hashlib.sha256(session_id.encode()).digest()
    rng = random.Random(int.from_bytes(seed, 'big'))
    rng.shuffle(ordered)
    trials = [dict(c, trial_id=f'original-{i}', repeat_of=None) for i, c in enumerate(ordered)]
    # Only choose early originals so repeats at the end have enough separation.
    candidates = list(trials[:max(0, len(trials)-3)])
    rng.shuffle(candidates)
    for i, item in enumerate(candidates[:min(repeat_count, len(candidates))]):
        trials.append(dict(item, trial_id=f'repeat-{i}', repeat_of=item['trial_id']))
    return trials


def completion(trials, records, session_id, protocol_hash):
    responses = {r.get('trial_id'): r for r in records if r['session_id'] == session_id and r.get('protocol_hash') == protocol_hash and not r['mock']}
    counts = {'completed': 0, 'skipped': 0, 'unanswered': 0, 'total': len(trials)}
    for t in trials:
        r = responses.get(t['trial_id'])
        counts['unanswered' if r is None else 'skipped' if r['choice'] == 'skip' else 'completed'] += 1
    return counts


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--folder', default='artifacts/review_bundles')
    p.add_argument('--manifest', default='data/splits.csv')
    p.add_argument('--output', default='artifacts/review_plan.json')
    p.add_argument('--count', type=int, default=30)
    p.add_argument('--split', choices=['val', 'test'], default='val')
    p.add_argument('--final-test', action='store_true')
    args = p.parse_args()
    if args.split == 'test' and not args.final_test:
        p.error('Final held-out planning requires --final-test.')
    out = Path(args.output)
    if out.exists():
        p.error('Plan already exists. Use a new versioned output path; do not overwrite a frozen plan.')
    plan = freeze_plan(args.folder, args.manifest, args.count, split=args.split)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2))
    print('Frozen plan SHA-256:', plan_hash(plan))
