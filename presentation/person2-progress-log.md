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
