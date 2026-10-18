"""Investigator diagnostics and manifest checks, independent of model libraries."""
import csv
import hashlib
from pathlib import Path
from evaluation.review import validate_pair, METHODS


def audit_case(bundle):
    validate_pair(bundle)
    result = bundle[METHODS[0]]
    predictions = result['predictions']
    truth = result['query'].get('ground_truth')
    ordered = sorted(predictions, key=lambda p: p['rank'])
    classes = [p['class_id'] for p in ordered]
    overlap = []
    for a, b in zip(predictions, bundle[METHODS[1]]['predictions']):
        x = [r['image_id'] for r in a['references']]
        y = [r['image_id'] for r in b['references']]
        overlap.append({'class_id': a['class_id'], 'same_order': x == y,
                        'same_set': set(x) == set(y), 'overlap_fraction': len(set(x) & set(y)) / len(x)})
    return {'query_id': result['query']['image_id'], 'ground_truth': truth,
            'predicted_class': classes[0], 'correct': classes[0] == truth if truth else None,
            'truth_in_candidates': truth in classes if truth else None,
            'truth_in_top_two': truth in classes[:2] if truth else None,
            'top_score_gap': ordered[0]['score'] - ordered[1]['score'] if len(ordered) > 1 else None,
            'identical_reference_sets': all(x['same_set'] for x in overlap), 'overlap': overlap}


def verify_manifest(bundle, manifest_path, asset_root=None, verify_hashes=False, allowed_split='val'):
    """Validate IDs, partition, labels and optional exported image bytes.

    Hashes refer to original files; transcoded display images will not match.
    """
    validate_pair(bundle)
    with open(manifest_path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    required = {'image_id', 'relative_path', 'label', 'split', 'sha256'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('Manifest missing required columns or rows')
    by_id = {r['image_id']: r for r in rows}
    errors = []
    if len(by_id) != len(rows):
        errors.append('Manifest has duplicate image IDs')
    seen = {}
    for row in rows:
        digest = row['sha256']
        if not digest:
            errors.append('Manifest contains a blank image hash')
        if digest in seen and seen[digest] != row['split']:
            errors.append('Exact file hash occurs in multiple partitions')
        seen[digest] = row['split']
    result = bundle[METHODS[0]]
    q = by_id.get(result['query']['image_id'])
    if q is None or q['split'] != allowed_split:
        errors.append('Query is missing or not in the allowed evaluation partition')
    elif q['label'] != result['query'].get('ground_truth'):
        errors.append('Query label differs from manifest')
    items = [result['query']] + [r for m in METHODS for p in bundle[m]['predictions'] for r in p['references']]
    for item in items:
        row = by_id.get(item['image_id'])
        if row is None:
            errors.append('Unknown image ID: ' + item['image_id'])
            continue
        if 'class_id' in item and (row['split'] != 'gallery' or row['label'] != item['class_id']):
            errors.append('Reference is outside gallery or has an incorrect label: ' + item['image_id'])
        if verify_hashes:
            p = Path(item['image_path'])
            p = p if p.is_absolute() else Path(asset_root or '.') / p
            if not p.is_file():
                errors.append('Image unavailable: ' + item['image_id'])
            elif hashlib.sha256(p.read_bytes()).hexdigest() != row['sha256']:
                errors.append('Image hash mismatch: ' + item['image_id'])
    return {'passed': not errors, 'errors': sorted(set(errors)), 'hashes_checked': verify_hashes,
            'manifest_sha256': hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
            'allowed_split': allowed_split,
            'limitation': 'File disjointness does not establish slide/patient independence.'}
