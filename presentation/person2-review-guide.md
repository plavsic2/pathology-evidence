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


## Failure browser and provenance gate

The Failure review page is investigator-only. It filters saved cases by incorrect prediction, correct class outside candidates, or identical reference sets, and displays reference overlap plus the top-score gap. The gap is descriptive, not calibrated uncertainty. Opening a case marks it exposed for the same browser session.

Blinded non-mock submission now requires the authoritative split manifest: set SPLIT_MANIFEST (default data/splits.csv). It checks query partition and labels, gallery IDs/labels, duplicate IDs and exact hashes crossing partitions. Development expects val; set REVIEW_SPLIT=test only after method freeze for a planned final evaluation. These checks verify identifiers and manifest consistency. Optional original-file hashing is available in the failure browser; converted demo PNGs will not match source TIFF hashes. Patient independence is still not established.

Person 2 can prepare saved pairs with python -m evaluation.prepare_review --limit 30. It calls the existing engine and changes no backend interface. This convenience sample is the first sorted validation IDs, not an unbiased expert-review design; agree on case selection before formal review. Test preparation requires both --split test and --final-test. The adapter copies original image files into its images/ subfolder, writes relative paths in the saved responses, and includes splits.csv from the cached manifest. Keep the folder intact when copying it and point SPLIT_MANIFEST at this manifest copy; compare its hash with the authoritative team manifest. Both method responses must identify the same query.

Investigator exports now include review_dashboard.html, a standalone count display suitable for presentation preparation. Empty real-review data produces an explicit no-results message. The failure page can download a self-contained comparison HTML with embedded images and the exact response-pair fingerprint; it reveals methods and labels and must stay separate from blinded review.

Remaining work: actual artifacts, clinician feedback, case-sampling agreement and final evaluation. No clinical outcome is claimed from these tools.


## Version 1.1 reviewer workflow

The implemented protocol is in evaluation-protocol.md; it supersedes the earlier MVP-only workflow descriptions above. Use streamlit run app/reviewer_app.py for reviewers and the original entrypoint for investigators. The reviewer entrypoint registers only the review page. Read instructions and submit a practice response in Demonstration before switching to real data, using the same anonymous session ID.

Freeze a case list with python -m evaluation.review_plan after actual pairs and the agreed manifest exist. Set REVIEW_PLAN to the resulting JSON file, REVIEW_BUNDLE_DIR to the response folder and SPLIT_MANIFEST to the matching manifest. Formal reviewer-only saving requires that plan. Without it, investigator-mode reviews are labelled exploratory. Keep saved bundles immutable after freezing. The planner defaults to 30 original cases with seed 42, two thirds random and the rest lower score-gap cases. These cohorts must be reported separately. Planned repeated trials are excluded from main counts and compared by method preference.

Reference image size affects both panels equally. Enlarged inspection supports query/reference selection without exposing paths or labels beyond the displayed candidate categories. Completion tracks saved, skipped and unanswered trial instances, not unique clinical cases. Export using python -m evaluation.export_review --db artifacts/reviews.sqlite3 --plan artifacts/review_plan.json --output results/review. Completion export covers started sessions only; people who never begin require a separate recruitment count.

Review records now retain protocol hashes, trial IDs, repeat links, cohort, and an optional potentially-misleading-reference response. That response is exploratory opinion, not proof of harm. Legacy records remain readable. Different plans/protocols must be reported separately. See person2-judge-outline.md for presentation preparation.

The dedicated reviewer entrypoint requires Streamlit 1.36 or newer for explicit page registration; requirements.txt reflects this minimum. It retains the existing framework and adds no new package. Reviewer-only mode checks original image hashes before accepting preferences. Use original exported files; missing, corrupted or converted files can be skipped but are not accepted as preference evidence.
