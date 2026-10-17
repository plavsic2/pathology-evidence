# Person 2 progress and decision log

Owner: plavsic2, Person 2 — Evidence Interface and Evaluation  
Project: Evidence-Grounded Tissue Classification with CONCH  
Started: October 17, 2026. Dates use America/Chicago.

## Purpose and recording rules

Record what we built, why we made decisions, what we learned, and the evidence supporting our presentation. Both teammates can read this log. This records work performed by the user with Codex assistance; it does not imply every implementation or test was performed manually by the user.

Append an entry after each meaningful implementation, experiment, or scope decision during active project work. Do not silently rewrite previous conclusions: append corrections and link the relevant commit or result. Mark each item as completed, observed, planned, proposed, blocked, or superseded. A plan is not a result, and mock data is not pathology evidence. No background updates are implied.

## Team boundaries and agreed decisions

| Decision | Agreement | Reason |
| --- | --- | --- |
| Ownership | Person 1, SVYDYA123: ML pipeline and evidence engine. Person 2, plavsic2: interface, evaluation, figures and presentation. | Allow independent development with minimal overlap. |
| Repository | This repository is the single source of truth. | Keep both teammates on a common version. |
| Dataset | Proposed 3,150 images: 1,800 train, 225 validation, 675 gallery, 450 test, provided sufficient usable data exists. | Establish a manageable prototype with distinct partition roles. |
| Split manifest | Person 1 generates and commits it once; do not change it after embedding begins without discussion and rebuilding affected artifacts. | Preserve vector alignment and experimental comparability. |
| Integration | Freeze analyze_query() and its JSON schema for the MVP; discuss changes together first. | Protect independent implementation and integration. |
| Shared artifacts | One shared Delta directory for embeddings, classifier and results. Exact path still pending agreement. | Avoid inconsistent copies and duplicate computation. |
| Scope | CONCH tissue-category comparison; no FPGA work. | Keep effort on the chosen workflow and evaluation. |
| Evaluation | Tune on validation; reserve test for final evaluation. | Avoid selecting methods using final results. |

See [COLLABORATION.md](../COLLABORATION.md) for the shared agreement.

## October 17, 2026 — Scope and evaluation design

**Status: completed planning; implementation pending.**

We reviewed the proposal and technical contract and confirmed our role as Person 2. The intended contribution is to help users inspect competing tissue categories using labeled references, and evaluate whether comparative retrieval adds useful information.

Decisions:
- Develop against mock or saved backend responses instead of depending on live CONCH inference.
- Preserve the backend contract and split configuration.
- Compare class-aware nearest neighbors against contrastive reranking using the same queries, gallery, candidates and reference counts.
- Separate embedding-based properties from expert judgments of usefulness.
- Describe references as comparative examples, not proof of classifier reasoning.
- Treat nine tissue categories as tissue categories, not nine clinical diagnoses.

Why this matters for judges: the project has a testable question beyond classifier accuracy. The question is whether the retrieved examples are useful for comparison, including when the model is wrong.

Evidence: the project discussion and imported starter source. No user study, expert preference finding, or performance improvement has been established.

## October 17, 2026 — Shared repository established

**Status: completed.**

- Created the private repository under plavsic2.
- Imported starter source without changing the analysis schema or split configuration.
- Added the collaboration agreement.
- Sent an invitation to SVYDYA123. It was pending acceptance when sent; acceptance has not been rechecked for this entry.
- Excluded the ZIP's synthetic validation/test result files from the initial commit so they cannot be mistaken for actual pathology findings.

Evidence: [starter import commit](https://github.com/plavsic2/pathology-evidence/commit/aab37217d128e5523a9769df668caa233e83a7cb).

Verification performed: all 14 Python source files parsed successfully; the extracted JSON files parsed successfully.
Verification not performed: automated runtime tests, actual CONCH endpoint calls, Delta integration, real-data evaluation. The local runtime lacked several project dependencies.

## October 17, 2026 — Interface issues identified in source review

**Status: observed; fixes pending.**

| Finding | Consequence | Planned action |
| --- | --- | --- |
| Query picker displays the dataset label even with ground truth hidden. | A reviewer can see the answer before judging examples. | Remove labels from picker text in review mode. |
| Mock response has empty image paths and fabricated scores. | Layout development is possible, but meaningful visual comparison is not. | Add clearly marked demonstration assets without presenting them as pathology results. |
| Existing screen shows one named method at a time. | It does not support blinded comparison. | Add anonymous A/B panels with persisted randomization. |
| Existing evaluation reports embedding similarity, margins and a diversity proxy. | These do not establish clinical usefulness; margins are optimized by reranking. | Add a separate reviewer protocol and response capture. |
| Ground truth remains in the frozen backend response. | Hiding it requires care across all review surfaces, including raw JSON. | Keep it concealed in blinded UI; do not change schema unilaterally. |

These findings came from reading code, not from a completed interactive application test.

## Ambition roadmap within Person 2 ownership

All items below are planned, not delivered.

| Improvement | Benefit | Dependency on Person 1 |
| --- | --- | --- |
| Blinded A/B comparison | Test reference usefulness beyond the model's own ranking score. | Existing outputs for both methods. |
| Prediction-hidden inspection mode | Support inspection before revealing the AI suggestion. | Existing query, predictions and references. |
| Failure-case browser | Show incorrect predictions, omitted correct categories and unhelpful references. | Saved predictions and evaluation labels. |
| Reproducible review records | Trace reviewer choices and figures to exact inputs. | Existing outputs; review-side metadata can be stored separately. |
| Presentation evidence export | Capture side-by-side examples, results and limitations. | Available saved results and images. |

Do not add another model, whole-slide processing, automated morphology detection or a new backend service to achieve these goals. Any schema-affecting proposal must be discussed first. Metadata owned by the review workflow can be recorded separately from analyze_query().

## Planned evaluation protocol

- Use validation queries during development.
- Compare equal numbers of references for identical candidate categories.
- Randomize A/B placement and save the mapping separately from reviewer-visible fields.
- Hide method names, ranking scores, query ground truth and raw response JSON during blinded review.
- Ask: "Which reference set better helps you compare these candidate tissue categories?"
- Offer A, B, tie, and neither useful, plus an optional reason.
- Separate ordinary queries from a predefined difficult-case subset; record selection rules.
- Record reviewer role, number of reviewers, number of queries, missing responses and repeated reviews using non-identifying reviewer IDs.
- If a pathology mentor is unavailable, report usefulness as unverified. Team preferences are not clinical validation.
- Report counts and limitations. Do not treat repeated reviews from one person as independent clinical experts.
- Measure top-two or top-three recall before interpreting a restricted candidate comparison.
- Preserve negative findings: no difference, identical references, or misleading examples.
- A formal claim that the interface improves user accuracy or reduces automation bias requires a separately designed study.

## Next checklist

- [ ] Agree on the exact shared Delta artifact directory.
- [ ] Person 1 generates and commits the authoritative split manifest before embedding.
- [ ] Create a separate Person 2 implementation branch from current main.
- [ ] Fix label visibility across the picker and review screen.
- [ ] Improve demonstration assets and keep mock status obvious.
- [ ] Implement blinded A/B review without changing the backend schema.
- [ ] Persist reviewer responses and randomized method mappings.
- [ ] Add meaningful checks for blinding, comparison consistency and saved review records.
- [ ] Run the interface with mock data and record actual verification.
- [ ] Integrate real validation outputs.
- [ ] Obtain preliminary expert feedback if available.
- [ ] Freeze evaluation choices before final test.
- [ ] Prepare figures, representative successes and failures, and a backup demo.

## Evidence to collect for the judges

| Claim we might make | Evidence required before claiming it |
| --- | --- |
| We built an inspectable comparison workflow. | Working demo, screenshots and implementation commit. |
| The review was blinded. | Verified UI behavior, randomized assignment records and protocol. |
| Comparative references were preferred. | Actual reviewer counts, ties, neither responses, sample selection and reviewer qualifications. |
| The method improves classification. | A controlled classification comparison; the retrieval UI alone does not show this. |
| The tool generalizes to new patients. | A verified patient-independent evaluation cohort; a disjoint tile split is insufficient. |
| The demo operates offline. | A successful run with exported images and cached artifacts, without live endpoint access. |

## Template for future entries

### YYYY-MM-DD — Milestone or decision

- Status:
- Work completed:
- Decision and rationale:
- How it strengthens the project:
- Ownership and agreement check:
- Verification actually performed:
- Result, including negative findings:
- Evidence: commit, figure, review record or result file:
- Limitations and remaining questions:
- Next action:

Do not include secrets, API keys, identifying reviewer details or unapproved patient data.

## October 17, 2026 — Organizer links checked

**Status: Box guide reviewed; Slack messages not accessed.**

Reviewed the [Box resource outline](https://uofi.app.box.com/s/vsl57eshv213e6gzcovj01umzt61wp69/file/2522592632731) in the browser. Box identifies it as updated October 12, 2026; its contents match the resource guide previously read from the ZIP.

Confirmed: contrasting examples for education are an organizer-suggested application; judging covers innovation, development progress, clinical impact and communication; the guide specifies October 21 submission of an abstract, availability and a stand-alone presentation with no more than 20 main slides. Schedule changes are to be announced through Slack.

The guide describes preloaded CONCH/MUSK resources but does not establish the current endpoint, credentials, service availability, team artifact path, or actual dataset counts.

The supplied [Slack channel](https://app.slack.com/client/T0C8M0NR3J4/C0C7W9RKMSQ) redirected to workspace sign-in. No channel messages or current announcements were read. Slack integration was offered as an access option; connection remains unconfirmed.

Decision: retain the agreed MVP and comparison evaluation. Do not change the backend schema, split or compute assumptions based on unread messages. Check current Slack announcements once access is available.

## October 17, 2026 — Slack access established and compute guidance reviewed

**Status: completed read-only review; no cluster access or implementation claimed.**

Read the supplied #all-hackathon channel and its referenced #compute-issues channel after Slack was connected. This supersedes the previous access limitation.

Verified organizer announcements:
- Hosted pathology models are scheduled through Sunday, October 18 at 6 p.m. Central. Calls must originate inside Delta. Cache required embeddings and export permitted demo assets before service closure.
- The shared service is intended for up to a few thousand tiles; whole-dataset jobs should use team GPU allocations. Our proposed 3,150-image extraction should respect service capacity and organizer guidance.
- Team outputs may use /work/nvme/bfqi/teams/<team-name>. The exact team directory remains a team decision, not yet configured.
- /work/nvme is not backed up, and the hackathon directories are readable by other participants. Keep credentials and private material out; back up permitted artifacts appropriately.
- Organizers reported /work/hdd filesystem problems and advised avoiding it.
- Login nodes were unstable/rebooted during the afternoon. At 3:47 p.m. Central, the technical organizer reported login02 and login03 looking better. This is a timestamped report, not a guarantee of current availability. Interactive Open OnDemand applications were suggested as an alternative.
- Quilt is available as a shared read-only resource. We are not expanding our agreed CONCH/CRC MVP to add it.
- Use a single model per experiment; embeddings from different models are not interchangeable.

Sources: [hosted models announcement](https://app.slack.com/archives/C0C7W9RKMSQ/p1792241751791109), [storage guidance](https://app.slack.com/archives/C0C7W9RKMSQ/p1792244622730939), [technical channel](https://app.slack.com/client/T0C8M0NR3J4/C0C7SRT9QJ2).

Decision: prioritize cached/offline compatibility and continue Person 2 development with mocks while Person 1 establishes real artifacts. No schema or split changes. Credentials seen in Slack are intentionally not reproduced in the log or repository.

## October 17, 2026 — Person 2 blinded review MVP implemented

**Status: implemented and locally tested on person2/blinded-review; pending merge and real-data integration.**

Delivered:
- Replaced the development screen with an independent comparison workflow: abstract mock fixtures, saved response pairs, and lazy loading of the cached backend.
- Removed answer-bearing query labels from selection, and removed source IDs, filenames, raw JSON, scores and method names from blinded displays.
- Sorted candidate categories alphabetically to avoid revealing classifier rank.
- Added deterministic per-session A/B assignment, anonymous role capture, tie/neither responses and optional comments.
- Added SQLite persistence keyed by reviewer session and exact response-pair SHA-256. Re-submission replaces a prior response instead of double counting it.
- Disabled submission when required images are missing or a case has been unblinded in that browser session.
- Added investigator-only CSV, summary JSON and Markdown count-table export. Mock responses are excluded; spreadsheet formula text in comments is escaped.
- Added pair-comparability validation and a review protocol guide.

Agreement check: no src/ backend files, analyze_query() schema, split settings, or manifest changed. The two-response saved bundle is a Person 2 wrapper around unchanged backend results. No Delta SSH access needed for development.

Professional decisions: use Streamlit's AppTest to verify interaction behavior rather than relying only on screenshots; use standard-library SQLite for durable, duplicate-resistant records; record exact input fingerprints for traceability; avoid confidence claims from ranking-score improvement.

Verification: 4 review-logic unit tests and 1 Streamlit AppTest scenario passed (5 total). AppTest covered mock rendering, no truth checkbox/raw JSON in initial blinded mode, successful tie submission, blocking previously exposed cases, and empty saved-bundle handling. A separate smoke check verified investigator export, mock exclusion and spreadsheet formula escaping. A missing cached engine was also checked without an application crash. Changed Python files parse successfully.

A Windows SQLite file-lock failure in the first unit-test run revealed unclosed database connections. Explicit connection closing fixed it; the tests were rerun successfully. A test script path was also corrected before the final successful run.

Limitations: automated interaction checks are not visual browser QA or clinical evaluation. No actual pathology images, expert reviews or real CONCH outputs have been evaluated. Blinding is a workflow aid, not security against source inspection/session resets. Reviewer sessions are self-reported identities. Saved response provenance must be checked against the shared manifest. Use a designated review host and persistent writable storage for the MVP.

Still pending: true image assets, shared Delta path, real validation integration, failure-case browser, automated plots, expert feedback and final held-out evaluation. No clinical usefulness improvement is claimed.

## October 17, 2026 — Failure inspection, provenance and presentation exports

**Status: implemented on Person 2 branch; tested with mock and temporary abstract images; pending real artifact integration.**

- Added investigator failure review with incorrect-prediction, missing-correct-candidate and identical-reference-set filters. Shows per-class overlap and descriptive classifier score gap.
- Added manifest verification for IDs, query split, labels, gallery membership, cross-partition exact hashes and optional original-image hashing. Non-mock blinded review saving now requires a passing manifest check. Validation remains the development default.
- Added a Person 2 adapter that calls the unchanged cached engine, exports both responses, copies original images with portable relative paths and includes a cached-manifest copy. Test export requires explicit final-test acknowledgement. Actual Delta execution of this adapter remains unverified.
- Added self-contained investigator comparison HTML exports with embedded images and response fingerprints. Added a count dashboard that explicitly reports no findings when no non-mock reviews exist.
- Extended protocol documentation. No backend, split configuration or shared manifest changed.

Verification: 11 tests passed (9 logic/export/provenance tests and 2 Streamlit AppTest scenarios). A separate AppTest smoke check using temporary solid-color images verified saved-pair loading, successful review submission with a valid manifest, disabled submission after removing the manifest, and a populated investigator page without exceptions. These fixture images are not pathology data and are not committed as experimental findings.

Visual QA: opened the local Streamlit preview in the browser and inspected the main comparison page, side-by-side fixture references and review controls. The investigator page was checked through AppTest; visual review with actual pathology images is still needed.

Professional rationale: compare method outputs without quietly rewriting rankings; identify identical-output cases; require partition provenance before accepting real reviews; keep investigator evidence separate from blinded evaluation; preserve portable evidence and explicit negative findings.

Remaining external dependencies: teammate's actual artifacts and authoritative manifest, shared storage path, agreed review sample, and domain reviewer feedback. No accuracy, preference or clinical benefit result is established. Presentation materials can now be exported from future real review records instead of fabricated examples.

## October 17, 2026 — Swiss-style typography and Catppuccin Mocha theme

**Status: implemented on Person 2 branch and visually checked.**

User requested a Swiss Knife or similar font and Catppuccin colors. Applied a local Helvetica Neue / Helvetica / Arial / sans-serif stack for a Swiss-style look, rather than bundling a commercial font. Added Catppuccin Mocha backgrounds, lavender accents, readable foregrounds, cyan focus outlines and shared styling for both comparison and investigator pages.

Verification: both existing Streamlit interface behavior tests passed after styling. Visually inspected the comparison screen in the local browser and adjusted caption contrast. No backend logic, response schema, split, manifest or ranking behavior changed.

## October 17, 2026 — Approved black-and-yellow palette

**Status: implemented following user approval of the palette preview.**

Replaced Catppuccin Mocha colors with warm black #101010, panels #191919, borders #343434, golden yellow #F5C518, hover/focus #FFDA47, text #F2F0E8 and secondary text #AAA79D. Kept the Swiss-style font stack and identical A/B panel treatments. Original tissue image colors are untouched. Backend, schema, splits and review behavior unchanged.

Verification: Python styling source and TOML theme configuration parse. Browser preview checked. This is a presentation-only change; no new experiment results are implied.

## October 17, 2026 — Reviewer onboarding and protocol package

**Status: implemented and checked on Person 2 branch; no real reviewer outcomes claimed.**

Delivered the additional scope requested:
- Reviewer instructions with defined A/B, tie, neither and skip meanings. Abstract practice must be acknowledged and submitted before real review; readiness persists by anonymous session and instruction version.
- Reference size controls applied equally to both sides, plus a selectable enlarged image inspector. No new image information is inferred.
- Deterministic reviewer schedules, optional spaced repeat trials, separate original/repeat records, and method-normalized consistency checks. Repeat trials never inflate primary preference counts.
- Progress counts for completed, skipped and unanswered trial instances. Investigator export can use the plan to report completion for sessions that have started. Nonstarters require a separate recruitment count.
- Optional potentially-misleading-reference feedback mapped to method and explicitly treated as exploratory opinion.
- Dedicated reviewer_app.py entrypoint registering only the review page; exploration/investigator navigation is absent. It is workflow separation, not account-level security.
- A versioned protocol and non-overwriting frozen-plan utility. Default sampling is two thirds seeded random, remainder lower top-score-gap cases; cohorts are reported separately. Actual case-list freezing waits for real artifacts.
- Formal reviewer mode verifies manifest identity, frozen response fingerprints and displayed original image hashes. Corrupt/missing images disable preferences and can be skipped when metadata is valid.
- Presentation content scaffold and backup-demo checklist.
- Review forms are keyed per trial so an earlier preference does not become a default on the next case.

Verification: all 17 Person 2 tests passed, including a temporary-image end-to-end scenario covering practice, frozen sampling, successful skip tracking, corrupt-image blocking, preference reset on a new trial and detection of modified frozen responses. A browser inspection confirmed readable practice instructions, image controls, black/yellow styling and no investigator links in reviewer-only mode. Tests use abstract fixtures only.

The first interface test after these changes caught a positional selector that no longer identified the source control; changed it to use its label and reran successfully. No clinical findings were inferred from test fixtures.

Agreement check: no backend source, analyze_query() response schema, dataset split settings or shared split manifest changed. Streamlit's existing minimum dependency was raised from 1.32 to 1.36 because the dedicated reviewer entrypoint uses explicit page registration. No new runtime package was added.

Remaining dependencies: actual artifacts, agreed shared directory, real frozen case list, domain feedback and final data evaluation. These additions provide the tools and protocol; they do not prove usefulness, diagnostic accuracy, patient independence or reduced harm.
