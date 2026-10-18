# Multi-candidate visual evidence integration

Integrated Person 1 backend commit `8625bab733335ce5431b98c735b9172e85ffbf0e` without changing `analyze_query()`, splits, ranking parameters, or the frozen reference-review plan.

## Launch

In the activated environment, configure the host's `ARTIFACT_DIR` and `DATA_ROOT` as in the Delta integration guide. Set `LUMEN_API_KEY` in the process environment using your existing credential mechanism. Do not put its value in source, shell scripts, screenshots, logs, a shared directory, or GitHub. The UI does not ask for or display the key.

```bash
streamlit run app/evidence_app.py --server.address 127.0.0.1
```

The investigator app also includes a **Visual evidence** page. The dedicated reviewer app does not expose it. For a portable local case preview, `EVIDENCE_BUNDLE_DIR` points to an exported paired-response folder; it defaults to `artifacts/priority_validation`. The screen uses the contrastive response and its first three candidates/references. Saved case paths are resolved to original local files before explanation generation. Cached backend mode calls the existing `analyze_query` method with three candidates and three references per candidate, validation only.

## Behavior

- Query plus three candidate tissue types, with three original reference images per candidate when provided by the backend.
- Reference labels B/C/D follow the explanation prompt's image order; A is the query. The images can be enlarged in the inspector.
- Supporting and contrasting observations are grouped per candidate. Empty supporting lists explicitly report no specific supporting similarities, without inventing positive evidence.
- `explanation_unavailable=true` shows **Visual explanation temporarily unavailable** and retains references. Missing credentials, top-level backend errors, API failures and malformed responses do not expose secrets or raw errors in the UI.
- Generation is explicit. Changing image size or inspecting references does not make another request; results are retained per exact analysis in browser session memory. A changed case gets its own observations. No explanation text or keys are automatically written to disk or GitHub.
- Main view hides model names, numerical classifier scores, raw JSON, source IDs and the dataset ground truth. Research-only disclaimer and machine-generated observation caveat remain visible.

## Joint smoke test

1. Run on a host with configured environment and readable images. Choose **Cached backend** or an exported saved case.
2. Confirm one query and nine reference images. Generate visual observations once; verify each statement against the images. Allow for up to three sequential API requests (the backend uses a 45-second timeout per candidate).
3. Check a candidate with `explanation_unavailable=true`: its references remain visible with the required message. Check a case with no supporting observations: no generic positive observations are invented by the UI.
4. Enlarge images and switch cases; ensure no automatic extra generation, no inherited text from another case, and no scores/model names in the main screen.
5. Do not use this explanation-enhanced screen to collect preferences under the frozen reference-only protocol. Its effects would require a separate evaluation design/version.

Local automated checks use simulated observations and failures, not live API calls or clinical interpretation. An authorized live UI smoke test passed on October 18: one saved validation query, three candidate requests, and all three structured observation responses rendered successfully. Reference enlargement preserved the observations without a new generation. No Delta GPU allocation was started; hosted-service accounting was not measured. The authenticated local preview runs on port 8506 while its process is alive. Further domain review and broader service testing remain outstanding. Generated statements are not verified findings, classifier reasoning, or proof of a tissue category.
