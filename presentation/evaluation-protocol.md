# Reference usefulness review protocol version 1.1

Status: validation case list and dataset fingerprints frozen on October 17, 2026, before real reviews. See review-val-v1-plan.json and reviewer-session-checklist.md. Reviewer recruitment and outcomes remain pending. This is an internal protocol, not a registered clinical study.

## Question and endpoints

Primary question: which retrieval method provides more useful reference examples for comparing the displayed candidate tissue categories? The primary endpoint is A/B preference mapped back to method, with tie and neither counted explicitly, on the seeded random cohort. Classifier predictions do not change between methods.

Secondary descriptive endpoints: preferences on difficult cases, skips and unanswered trials, identical-reference-set frequency, and agreement on repeated trials. The optional question about potentially unsupported interpretations is exploratory reviewer feedback, not a measured diagnostic error or harm rate.

## Sampling before review

Prepare validation response pairs with the unchanged cached engine. Verify all pairs against the authoritative manifest. Default target: 30 original cases, or all available if fewer. Seed: 42. Select two thirds by a seeded random ordering of the available exported pool. Select the remainder from unselected cases with the smallest top-two classifier score gap. This is a fixed sampling rule, not a calibrated definition of uncertainty. The exported pool itself may be a convenience subset; disclose its construction.

Frozen validation v1 uses the full 225-query validation metadata pool, 20 random cases, 10 additional lowest-score-gap cases and two repeats. The utility `evaluation.prepare_cohort` copies only selected images and verifies their original hashes. Plan fingerprint: `e1f07276281b9f13da84c66d097044e042bd7c54eadeb2c718be4943c388916d`. Random selection represents this tile-level validation pool, not independent patients or a clinical population. No preference results were used for selection.

Freeze using `python -m evaluation.review_plan --folder artifacts/review_bundles --manifest data/splits.csv --output artifacts/review_plan.json --count 30`. It refuses to overwrite an existing plan. The plan stores cohort tags, each response fingerprint, the manifest hash and repeat count. A response change requires a new plan version. Do not replace low-quality or unfavorable cases after reviews start. Record technical exclusions separately.

Final test use requires a distinct plan and explicit final-test acknowledgement after method weights are fixed. Development remains validation-only. A plan must match the chosen review split and manifest. Reviewer-only saving also verifies displayed original-file hashes; converted or missing assets block preference saving and can be recorded as skipped trials. Do not mix validation/test or different plan versions in one claimed endpoint.

## Reviewer workflow

1. Use a non-identifying session ID and self-reported role. Do not collect names or patient details in free text.
2. Read the instructions, acknowledge them and complete the abstract practice case. Practice does not measure pathology ability and is excluded from outcomes.
3. Launch `streamlit run app/reviewer_app.py` on the designated reviewer host. This entrypoint registers only the reviewer page and removes investigator navigation and exploration mode. Keep investigator tools on a separate session/process. This is separation of workflow, not authentication or a guarantee against source inspection.
4. View the query and equal candidate categories/reference counts. Candidate categories are alphabetical. Method names, query labels, scores, IDs and raw JSON are hidden. A/B assignment is deterministic per session, exact pair and trial.
5. Use equal reference display size and enlarged inspection as needed. Zoom changes display size, not native resolution or specimen magnification.
6. Select A, B, tie (equally useful) or neither (both unhelpful), with an optional reason. Skip if unable to judge; skip is distinct from neither. Missing images disable preference saving but can be skipped if provenance and onboarding are valid.
7. Optionally indicate which side could encourage an unsupported interpretation. No correctness or method feedback is shown during review.

Readiness is stored for a session and instruction version. A new protocol version should trigger renewed onboarding. Do not open review cases in investigator tools first. Browser exposure checks are additional safeguards only.

## Repeated cases

For a sufficiently large plan, add up to two repeated trials, with at least three intervening trials after the original. Pools smaller than four have no repeats. Reviewers are told repetition may occur but individual repeat positions are not identified. Assignment may swap A/B. Store trial IDs and original-repeat links separately from the frozen engine output. Compare normalized method preferences, including tie/neither, rather than screen letters. Skipped pairs are not included in repeat agreement. Repeat trials do not increase main preference counts.

## Persistence and reporting

One saved record per session, plan and trial; a resubmission replaces that record. Store choice, normalized preference, optional misleading feedback, role, timestamp, cohort and exact input fingerprint. Retain old records under their old protocol identifiers. Practice and repeat records stay traceable but are excluded from primary counts.

With `--plan artifacts/review_plan.json`, the investigator export includes completed/skipped/unanswered counts for each session that has started saving trials. It cannot count people who never start; record invited/started reviewer counts separately without identifying details. Self-entered session IDs are not verified identities.

Report random and difficult cohorts separately; include ties, neither, skips, missing data, repeated trials and identical-output cases. Do not count multiple cases from one reviewer as independent experts. With a small convenience reviewer sample, use descriptive counts and a limitation statement rather than a general clinical efficacy claim. Report reviewer roles and sampling pool size. Keep different protocol versions separate.

## Dependencies and boundaries

Actual case selection, manifest identity, image readability, institutional permission requirements for any human study, and mentor availability still require checking. A small technical feedback exercise is not automatically clinical validation. No backend schema, original split manifest, ranking weights or model changes are authorized by this protocol.
