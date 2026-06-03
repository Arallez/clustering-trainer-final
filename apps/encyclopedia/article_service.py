from django.core.cache import cache

from .article_profiles import build_article_search_profile
from .article_ranker import rank_articles
from .article_sources import fetch_articles_for_profile


CACHE_TIMEOUT_SECONDS = 60 * 60 * 12


def get_recommended_articles_for_concept(concept, limit=20):
    profile = build_article_search_profile(concept)
    cache_key = f"concept_articles:v1:{profile.cache_fingerprint}:limit:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    articles = fetch_articles_for_profile(profile)
    ranked = rank_articles(profile, articles, limit=limit)

    payload = {
        "concept": {
            "id": concept.id,
            "title": concept.title,
            "kind": profile.kind,
        },
        "profile": {
            "queryEn": profile.query_en,
            "queryRu": profile.query_ru,
            "positiveTerms": list(profile.positive_terms[:16]),
            "contextTerms": list(profile.context_terms[:12]),
            "negativeTerms": list(profile.negative_terms[:12]),
        },
        "articles": ranked,
    }
    cache.set(cache_key, payload, CACHE_TIMEOUT_SECONDS)
    return payload
