"""Prepare and freeze a validation cohort from the full cached query pool."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from evaluation.review import fingerprint
from evaluation.review_plan import freeze_plan, plan_hash
from evaluation.case_audit import verify_manifest


def prepare(engine, manifest, output, count=30):
    out = Path(output)
    if out.exists():
        raise FileExistsError('Use a new versioned output directory')
    ids = sorted(engine.df.loc[engine.df.split == 'val', 'image_id'].astype(str))
    if len(ids) < count:
        raise ValueError('Not enough validation queries')
    # Metadata for the complete validation pool makes sampling independent of
    # the four investigator examples. Only selected original images are copied.
    with tempfile.TemporaryDirectory() as tmp:
        pool = Path(tmp)
        for i, qid in enumerate(ids):
            pair = {m: engine.analyze_query(qid, method=m) for m in ('class_aware', 'contrastive')}
            (pool / f'case_{i+1:04d}.json').write_text(json.dumps(pair))
        plan = freeze_plan(pool, manifest, count=count)
        out.mkdir(parents=True)
        (out / 'images').mkdir()
        shutil.copyfile(manifest, out / 'splits.csv')
        for case in plan['cases']:
            pair = json.loads((pool / case['file']).read_text())
            for result in pair.values():
                items = [result['query']] + [r for c in result['predictions'] for r in c['references']]
                for item in items:
                    original = Path(item['image_path'])
                    name = hashlib.sha256(item['image_id'].encode()).hexdigest()[:24] + original.suffix.lower()
                    target = out / 'images' / name
                    if not target.exists():
                        shutil.copyfile(original, target)
                    item['image_path'] = 'images/' + name
            check = verify_manifest(pair, manifest, out, verify_hashes=True)
            if not check['passed']:
                raise ValueError(str(check['errors']))
            (out / case['file']).write_text(json.dumps(pair, indent=2))
            case['bundle_sha256'] = fingerprint(pair)
        plan['preparation'] = 'Full validation metadata pool; original images copied and hash-verified after selection. No test queries.'
        (out / 'review_plan.json').write_text(json.dumps(plan, indent=2))
        print(f'Frozen {len(plan["cases"])} cases from {len(ids)} validation queries. Plan SHA-256: {plan_hash(plan)}')
        return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--manifest', default='data/splits.csv')
    args = parser.parse_args()
    from src.engine import load_engine
    prepare(load_engine(), Path(args.manifest), args.output)
