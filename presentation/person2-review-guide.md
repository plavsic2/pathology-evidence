# Person 2 reference review

## Run

Install the existing requirements, then run `streamlit run app/streamlit_app.py` from the repository root. Demonstration mode needs no CONCH, classifier artifacts, SSH or real images. Its abstract fixtures are not simulated tissue. Both demonstration methods intentionally show identical references.

The frozen backend schema and split configuration are unchanged. Cached engine mode lazily imports Person 1's engine and uses validation queries only. Missing engine dependencies do not prevent demonstration or saved-response development.

## Saved responses

Set `REVIEW_BUNDLE_DIR` to a directory of JSON files. Each file wraps two unchanged backend responses: `{"class_aware": <response>, "contrastive": <response>}`. This is a review-side container, not a backend schema change. Image paths may be absolute on the machine running Streamlit or relative to this directory. The same query, model metadata, predictions and per-candidate reference counts must appear in both responses. Missing images disable submission.

Only use trusted local response files. Saved-pair mode does not itself verify the originating data split or gallery membership: verify those against the shared manifest before formal review. Keep test pairs out of the development directory.

## Protocol

Use an anonymous session identifier for each reviewer. Reuse it when resuming; a new identifier counts as a different session. Do not put names or patient details in notes. Reviewer roles are self-reported.

Blinded mode hides query labels, candidate ranks and classifier scores, method names, source IDs, file paths, ranking scores and raw JSON. Reference categories remain visible so the user can compare them. Images are passed as bytes rather than answer-bearing filenames. Candidate categories appear alphabetically. A/B placement is deterministic for a session and exact response-pair fingerprint. A rerun does not reshuffle it.

Exploration mode reveals methods and optionally truth. Returning to blinded mode cannot submit the same exposed case in that browser session. This is a workflow safeguard, not access control: participants should not inspect source files, reset sessions, or switch modes for review cases. Use separate reviewer sessions and an investigator process for stronger blinding.

Save A, B, tie or neither, optionally with a reason. SQLite uses one record per session and response-pair fingerprint; resubmitting replaces that record. It records UTC time, role, exact bundle hash and hidden method assignment. Set `REVIEW_DB` to persistent writable storage; back it up. Both teammates should coordinate any shared database location and permissions. Avoid simultaneous SQLite writers on unsupported network filesystems; use one designated review host for the MVP.

## Investigator export

Run `python -m evaluation.export_review --db artifacts/reviews.sqlite3 --output results/review`. This produces raw CSV, counts JSON and a Markdown table suitable for presentation preparation. These outputs unblind assignments and must stay out of the reviewer view. Mock reviews are excluded from result counts. The export summarizes preferences, not diagnostic accuracy or clinical benefit.

## Before claiming success

- Verify data partitions and gallery provenance against the authoritative manifest.
- Define the review sample before inspecting method preferences.
- Include difficult cases and identical-output cases; do not select only attractive examples.
- Keep reference counts and candidate categories identical across methods.
- Record sample size, reviewer qualifications, repeated reviewers and limitations.
- Obtain pathology expertise before describing preferences as clinically meaningful.
- Freeze method weights before final test evaluation.

## Remaining extensions

Failure-case browsing, automatic plots, full contract validation, independent-patient evaluation and formal user-accuracy studies remain separate work. This implementation does not claim those features or outcomes.
