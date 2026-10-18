"""Handpicked validation cases for investigation, never an unbiased cohort."""
PRIORITY_CASES = {
    '70eccc3f2e78b00d': 'TUM vs NORM: nearly tied',
    '94394b287ecddee1': 'STR predicted as MUS',
    '11a3e8d3096d83e8': 'MUC predicted as TUM: high model score',
    'b1d78ff6551a8c8c': 'MUS predicted as STR: DEB also close',
}


def select_queries(manifest, split='val', query_ids=None, limit=30):
    available = set(manifest.loc[manifest.split == split, 'image_id'].astype(str))
    if query_ids is not None:
        selected = list(dict.fromkeys(query_ids))
        missing = set(selected) - available
        if missing:
            raise ValueError('Requested queries missing from selected split: ' + ', '.join(sorted(missing)))
        return selected
    return sorted(available)[:limit]
