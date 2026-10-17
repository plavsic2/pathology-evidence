# Team collaboration agreement

This repository is the single source of truth for the hackathon prototype.

- Person 1 (SVYDYA123): ML pipeline, embeddings, classifier, retrieval and backend artifacts.
- Person 2 (plavsic2): interface, evaluation, reviewer comparisons, figures and presentation.
- Keep the proposed 3,150-image split (1,800 train / 225 validation / 675 gallery / 450 test), provided sufficient usable data exists.
- Generate and commit data/splits.csv once. Do not change it after embedding begins without discussion and rebuilding affected artifacts.
- Freeze analyze_query() and its JSON schema for the MVP. Discuss schema changes together before implementing them.
- Choose one shared Delta directory for embeddings, classifier and results. Exact path: pending team agreement. Configure ARTIFACT_DIR consistently.
- Develop and tune using validation queries; reserve test queries for final evaluation.
- Keep credentials, raw images, embeddings and classifier artifacts out of Git.

## Starter status

The source is imported from the supplied starter ZIP without changing the analysis schema or split configuration. The ZIP's synthetic validation/test result files are intentionally excluded; they are not pathology experiment findings. Python syntax and JSON parsing were checked locally. Runtime tests and actual Delta/CONCH integration remain to be verified.

Known follow-up work: hide query labels in the picker during blinded review; add useful mock images; add blinded A/B review and run identifiers. Coordinate any schema-affecting changes first.
