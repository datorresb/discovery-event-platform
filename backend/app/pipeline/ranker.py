"""Cross-source frequency ranking.

Events mentioned by more independent sources get a higher score.
"""

from __future__ import annotations


def rank_clusters(clusters: list[dict]) -> list[dict]:
    """Score and sort event clusters by cross-source frequency.

    Each cluster dict has 'canonical', 'sources', 'source_count'.
    Adds a 'score' field (float, 0-1 normalized) and sorts descending.
    """
    if not clusters:
        return []

    max_sources = max(c["source_count"] for c in clusters)

    for cluster in clusters:
        cluster["score"] = cluster["source_count"] / max_sources if max_sources > 0 else 0.0

    return sorted(clusters, key=lambda c: c["score"], reverse=True)
