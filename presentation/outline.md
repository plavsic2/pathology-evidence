# Suggested presentation (6–8 slides)
1. Clinical motivation: classifier labels alone lack inspectable reference examples.
2. Problem scope: nine CRC tissue classes, not clinical differential diagnosis.
3. Pipeline: CONCH embeddings → logistic regression → per-class retrieval → contrastive reranking.
4. Retrieval comparison: global nearest, class-aware, contrastive.
5. Evaluation: accuracy, similarity, margin, diversity, optional blinded expert review.
6. Demo: clear case, ambiguous case, failure case.
7. Limitations: similarity ≠ explanation; label-level and tile-level leakage; not validated clinically.
8. Next steps: expert annotations, localized morphology, whole-slide evidence.
