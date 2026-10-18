# Running the frozen validation feedback session

Person 2 owns this workflow. Person 1 owns retrieval metrics. Neither the classifier nor the ranking weights change here.

## Prepare once

`python -m evaluation.prepare_cohort --output artifacts/review_val_v1`

This reads every validation query through the existing cached engine, selects 20 seeded random cases and 10 additional lowest-score-gap cases, copies only selected original images, verifies their hashes, and writes a non-overwriting plan. It does not load test queries or regenerate embeddings. Keep the entire folder intact. Do not change case membership after seeing reviewer preferences.

## Start the reviewer interface

From the project root in the activated environment (Linux syntax):

```bash
export REVIEW_BUNDLE_DIR="$PWD/artifacts/review_val_v1"
export REVIEW_PLAN="$REVIEW_BUNDLE_DIR/review_plan.json"
export SPLIT_MANIFEST="$REVIEW_BUNDLE_DIR/splits.csv"
export REVIEW_DB="$PWD/artifacts/reviewer_val_v1.sqlite3"
streamlit run app/reviewer_app.py --server.address 127.0.0.1
```

Use a host available to the reviewer, or have them review in person. A localhost address on your PC is not a remote invitation link. Keep the investigator application separate. The reviewer screen contains 30 original cases and two repeats (32 trials). Allow breaks; report skipped and unanswered trials rather than pressuring reviewers to finish.

## Before the session

- Ask a mentor/pathology trainee or expert for voluntary technical feedback. Keep a count of invited and started reviewers and their roles, without names in project logs. Follow any applicable institutional requirements before recruiting a formal study.
- Explain that this is an educational research prototype. The question is usefulness of references for comparing displayed categories; it is not a diagnostic-accuracy test.
- Use a new anonymous session ID. Read instructions, acknowledge them, and submit the abstract practice example before switching to Saved response pairs.
- Do not show labels, method identities, case-selection rationale, classifier scores or investigator views beforehand. Do not use developers already familiar with cases as independent blinded experts.

## After the session

- Preserve the SQLite database and frozen plan together. Export results using the existing export utility with its `--plan` option.
- Report random and difficult cohorts separately. Include tie/neither, skips, unanswered trials, repeat agreement, reviewer role and sample size.
- Capture positive and negative comments. Do not replace cases to improve outcomes. Reference overlap and logit margins are technical properties, not proof of usefulness.
- With no domain reviewers, present the workflow and technical checks as completed, and usefulness as unevaluated.

Next joint steps: compare feedback with Person 1's retrieval metrics, freeze any final engineering choices before held-out evaluation, prepare real-result figures, and rehearse the presentation and offline backup demo.
