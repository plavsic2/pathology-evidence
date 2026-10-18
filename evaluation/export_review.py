"""Export investigator-only review counts and CSV; never expose this in blinded UI."""
import argparse
import csv
import json
from pathlib import Path
from evaluation.review import read_reviews, summarize
from evaluation.evidence_export import summary_html
from evaluation.review_plan import schedule, completion, plan_hash


def export(db, output, plan=None):
    records = read_reviews(db)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary = summarize(records)
    (output / 'review_summary.json').write_text(json.dumps(summary, indent=2))
    with (output / 'review_responses.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['session_id', 'reviewer_role', 'query_id', 'bundle_sha256', 'choice', 'selected_method', 'note', 'mock', 'created_utc', 'protocol_hash', 'trial_id', 'repeat_of', 'cohort', 'misleading', 'misleading_method']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        # Neutralize spreadsheet formulas in reviewer-entered text.
        for r in records:
            writer.writerow({k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v) for k, v in r.items()})
    if plan is not None:
        protocol = plan_hash(plan)
        sessions = sorted({r['session_id'] for r in records if r.get('protocol_hash') == protocol and not r['mock']})
        completion_rows = [dict(session_id=session, **completion(schedule(plan['cases'], session, plan.get('repeat_count', 0)), records, session, protocol)) for session in sessions]
        with (output / 'review_completion.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['session_id','completed','skipped','unanswered','total'])
            writer.writeheader()
            for row in completion_rows:
                row = dict(row)
                if row['session_id'].lstrip().startswith(('=', '+', '-', '@')):
                    row['session_id'] = "'" + row['session_id']
                writer.writerow(row)
        summary['completion_for_started_sessions'] = completion_rows
        (output / 'review_summary.json').write_text(json.dumps(summary, indent=2))
    counts = summary['counts']
    report = '# Reference review results\n\n'
    report += f"{summary['n_reviews']} non-mock responses, {summary['n_reviewers']} reviewer sessions, {summary['n_queries']} queries.\n\n"
    report += '| Preference | Count |\n| --- | --- |\n' + ''.join(f'| {m} | {v} |\n' for m, v in counts.items())
    report += '\nPrimary random-cohort preference counts: ' + json.dumps(summary['primary_random_counts']) + '\n'
    report += f"\nSkipped original trials: {summary['skipped_original_trials']}. Repeat pairs compared: {summary['repeat_pairs_compared']}; method-level agreement: {summary['repeat_pairs_agree']}.\n"
    report += '\nMisleading-reference feedback (exploratory, not measured diagnostic harm): ' + json.dumps(summary['misleading_counts']) + '\n'
    report += '\nProtocol hashes: ' + ', '.join(summary['protocols']) + '. Report each protocol separately if multiple are present.\n'
    report += '\n' + summary['limitation'] + '\n\nReviewer qualifications are self-reported. Mock responses are excluded from these counts. Report sampling and reviewer roles alongside results.\n'
    (output / 'review_report.md').write_text(report)
    (output / "review_dashboard.html").write_text(summary_html(summary), encoding="utf-8")
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--db', default='artifacts/reviews.sqlite3')
    p.add_argument('--output', default='results/review')
    p.add_argument('--plan', help='Frozen review plan for unanswered/skipped completion export')
    args = p.parse_args()
    print(json.dumps(export(args.db, args.output, json.loads(Path(args.plan).read_text()) if args.plan else None), indent=2))
