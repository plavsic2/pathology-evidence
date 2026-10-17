"""Export investigator-only review counts and CSV; never expose this in blinded UI."""
import argparse
import csv
import json
from pathlib import Path
from evaluation.review import read_reviews, summarize


def export(db, output):
    records = read_reviews(db)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary = summarize(records)
    (output / 'review_summary.json').write_text(json.dumps(summary, indent=2))
    with (output / 'review_responses.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['session_id', 'reviewer_role', 'query_id', 'bundle_sha256', 'choice', 'selected_method', 'note', 'mock', 'created_utc']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        # Neutralize spreadsheet formulas in reviewer-entered text.
        for r in records:
            writer.writerow({k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v) for k, v in r.items()})
    counts = summary['counts']
    report = '# Reference review results\n\n'
    report += f"{summary['n_reviews']} non-mock responses, {summary['n_reviewers']} reviewer sessions, {summary['n_queries']} queries.\n\n"
    report += '| Preference | Count |\n| --- | --- |\n' + ''.join(f'| {m} | {v} |\n' for m, v in counts.items())
    report += '\n' + summary['limitation'] + '\n\nReviewer qualifications are self-reported. Mock responses are excluded from these counts. Report sampling and reviewer roles alongside results.\n'
    (output / 'review_report.md').write_text(report)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--db', default='artifacts/reviews.sqlite3')
    p.add_argument('--output', default='results/review')
    args = p.parse_args()
    print(json.dumps(export(args.db, args.output), indent=2))
