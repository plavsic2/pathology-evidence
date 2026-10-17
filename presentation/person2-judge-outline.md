# Person 2 presentation evidence outline

Use this alongside Person 1's methods/results slides. This is a content scaffold; bracketed fields must be replaced with verified facts before submission. Keep the combined team deck within the organizer's slide limit.

## Slide 1 The workflow problem

Explain the gap between a tissue label and useful comparison examples. Name the intended user and the task. Show a query and two candidate tissue categories once real images exist. Do not describe nine tissue categories as nine diagnoses.

## Slide 2 What Person 2 built

Show the actual interface: query, anonymous reference sets, equal display controls, practice instructions and preference choices. Explain that the backend contract and split remained stable so both teammates could work independently.

## Slide 3 How we tested usefulness

Show a simple sequence: verify provenance, freeze sample, complete practice, compare anonymous sets, save feedback, inspect failures. State the primary random-cohort endpoint and secondary difficult-case/repeatability analyses. Fill in [actual sampling pool], [cases], [reviewer roles], [started sessions], [completed/skipped/unanswered counts].

## Slide 4 Results

Insert the investigator dashboard for the chosen plan. Show preference counts, ties and neither; separate random and difficult cases. Include identical-output cases and repeated-trial agreement. If no expert feedback is collected, say so explicitly. Do not use mock records as results or claim that preference demonstrates improved diagnostic accuracy.

## Slide 5 A success and a failure

Export actual self-contained comparison pages. Explain why one example was useful according to feedback and show a misleading or unhelpful case. Tie every image to its source ID and response fingerprint in investigator evidence. Do not cherry-pick screenshots as the only evaluation.

## Slide 6 Limitations and next experiment

Discuss tile-level independence, convenience sampling, self-reported reviewer roles, small sample, workflow blinding limits and lack of diagnostic-outcome measurement. Propose an appropriately controlled future study of task correctness/time and potentially misleading evidence, without implying this study was performed.

## Demo backup checklist

- [ ] Real query/reference images and approved provenance available offline.
- [ ] Correct branch/commit and frozen plan hash recorded.
- [ ] Reviewer mode starts without investigator navigation.
- [ ] Practice uses clearly marked abstract fixtures.
- [ ] One successful case, one failure and one identical-output example captured.
- [ ] Record a short screen capture after real integration.
- [ ] Stand-alone slides explain all necessary results without live narration.
