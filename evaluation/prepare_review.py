"""Person 2 adapter: export paired responses from the existing cached engine."""
import argparse
import json
import hashlib
import shutil
from pathlib import Path
from evaluation.review import validate_pair


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', default='artifacts/review_bundles')
    p.add_argument('--split', choices=['val', 'test'], default='val')
    p.add_argument('--final-test', action='store_true', help='Explicitly acknowledge final held-out evaluation')
    p.add_argument('--limit', type=int, default=30)
    args = p.parse_args()
    if args.split == 'test' and not args.final_test:
        p.error('Test export requires --final-test; develop using validation only.')
    if args.limit < 1:
        p.error('Limit must be positive')
    # No new backend API: only two calls to the existing function.
    from src.engine import load_engine
    engine = load_engine()
    ids = sorted(engine.df.loc[engine.df.split == args.split, 'image_id'].tolist())[:args.limit]
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'images').mkdir(exist_ok=True)
    engine.df.to_csv(out / 'splits.csv', index=False)
    for i, qid in enumerate(ids):
        pair = {m: engine.analyze_query(qid, method=m) for m in ['class_aware', 'contrastive']}
        validate_pair(pair)
        for result in pair.values():
            for item in [result['query']] + [r for c in result['predictions'] for r in c['references']]:
                original = Path(item['image_path'])
                if not original.is_file():
                    raise FileNotFoundError('Missing export image: ' + str(original))
                filename = hashlib.sha256(item['image_id'].encode()).hexdigest()[:24] + original.suffix.lower()
                target = out / 'images' / filename
                if not target.exists():
                    shutil.copyfile(original, target)
                item['image_path'] = 'images/' + filename
        (out / f'case_{i+1:04d}.json').write_text(json.dumps(pair, indent=2))
    print(f'Exported {len(ids)} pairs from {args.split}. Images and a manifest copy are included; keep this folder intact.')


if __name__ == '__main__':
    main()
