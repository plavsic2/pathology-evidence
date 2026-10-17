"""Portable investigator evidence pages; never serve to blinded reviewers."""
import base64
import html
import io
from pathlib import Path
from evaluation.case_audit import audit_case
from evaluation.review import fingerprint


def case_html(bundle, asset_root='.'):
    from PIL import Image
    audit = audit_case(bundle)
    def image(item):
        p = Path(item['image_path'])
        p = p if p.is_absolute() else Path(asset_root) / p
        if not item['image_path'] or not p.is_file():
            return '<p>Image unavailable</p>'
        with Image.open(p) as im:
            im = im.convert('RGB')
            im.thumbnail((512, 512))
            buffer = io.BytesIO()
            im.save(buffer, format='PNG')
        return '<img alt="Dataset image" src="data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode() + '">'
    escape = lambda value: html.escape(str(value))
    body = '<h1>Tissue reference comparison</h1><p>Investigator export: labels and methods revealed. Not a diagnostic explanation.</p>'
    body += '<p>Query: ' + escape(audit['query_id']) + '; label: ' + escape(audit['ground_truth']) + '; prediction: ' + escape(audit['predicted_class']) + '</p>'
    body += image(bundle['class_aware']['query'])
    body += '<div class="sets">'
    for method in ['class_aware', 'contrastive']:
        body += '<section><h2>' + method + '</h2>'
        for c in bundle[method]['predictions']:
            body += '<h3>' + escape(c['class_id']) + '</h3><div class="refs">'
            for ref in c['references']:
                body += '<figure>' + image(ref) + '<figcaption>' + escape(ref['image_id']) + '</figcaption></figure>'
            body += '</div>'
        body += '</section>'
    body += '</div><p>Exact response-pair SHA-256: ' + fingerprint(bundle) + '</p>'
    body += '<p>Same reference sets across methods: ' + str(audit['identical_reference_sets']) + '. File and patient provenance must be verified separately.</p>'
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Tissue comparison evidence</title><style>body{font:16px system-ui;margin:32px;color:#162334}img{width:160px;height:160px;object-fit:contain}.sets{display:grid;grid-template-columns:1fr 1fr;gap:24px}.refs{display:flex;flex-wrap:wrap}figure{margin:8px}figcaption{max-width:160px;overflow-wrap:anywhere;font-size:12px}p{overflow-wrap:anywhere}@media(max-width:650px){.sets{grid-template-columns:1fr}}</style>' + body + '</html>'


def summary_html(summary):
    counts = summary['counts']
    n = summary['n_reviews']
    rows = ''.join('<tr><th>' + html.escape(k) + '</th><td>' + str(v) + '</td><td><meter min="0" max="' + str(max(n, 1)) + '" value="' + str(v) + '">' + str(v) + '</meter></td></tr>' for k, v in counts.items())
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Reference review counts</title><style>body{font:18px system-ui;margin:40px;max-width:950px}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd}meter{width:100%}</style><h1>Reference review counts</h1><p>' + (str(n) + ' non-mock responses.' if n else 'No non-mock reviews collected. No effectiveness result is available.') + '</p><p>' + str(summary['n_reviewers']) + ' reviewer sessions; ' + str(summary['n_queries']) + ' queries.</p><table><tr><th>Preference</th><th>Count</th><th>Share of all responses</th></tr>' + rows + '</table><p>' + html.escape(summary['limitation']) + '</p><p>Mock responses excluded: ' + str(summary['excluded_mock_reviews']) + '. Reviewer qualifications are self-reported. Counts are descriptive, not independent clinical validation.</p></html>'
