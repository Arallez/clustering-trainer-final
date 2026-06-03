import math
import re


MIN_RELEVANCE_SCORE = 8


def rank_articles(profile, articles, limit=20):
    scored = []
    for article in articles:
        score, reasons = score_article(profile, article)
        if score >= MIN_RELEVANCE_SCORE:
            scored.append((score, article, reasons))

    scored.sort(
        key=lambda item: (
            item[0],
            _year_as_int(item[1].year),
            item[1].citations,
        ),
        reverse=True,
    )

    return [
        {
            **article.as_dict(),
            "relevanceScore": round(score, 2),
            "relevanceReasons": reasons[:4],
        }
        for score, article, reasons in scored[:limit]
    ]


def score_article(profile, article):
    title = _normalize(article.title)
    abstract = _normalize(article.abstract)
    body = f"{title} {abstract}".strip()

    score = 0.0
    reasons = []

    negative_hits = _matched_terms(body, profile.negative_terms)
    if negative_hits:
        score -= 14 * len(negative_hits)
        reasons.append(f"штраф за нерелевантный контекст: {', '.join(negative_hits[:3])}")

    title_hits = _matched_terms(title, profile.positive_terms)
    body_hits = _matched_terms(body, profile.positive_terms)
    context_hits = _matched_terms(body, profile.context_terms)

    if title_hits:
        score += 8 * len(title_hits)
        reasons.append(f"термины темы в названии: {', '.join(title_hits[:4])}")
    if body_hits:
        score += 2.2 * len(body_hits)
        if not title_hits:
            reasons.append(f"термины темы в аннотации: {', '.join(body_hits[:4])}")
    if context_hits:
        score += 2.6 * min(len(context_hits), 5)
        reasons.append(f"контекст кластеризации: {', '.join(context_hits[:4])}")

    if _contains_any(title, ["clustering", "cluster analysis", "кластеризац", "кластерный анализ"]):
        score += 7
        reasons.append("кластеризация явно указана в названии")
    elif _contains_any(abstract, ["clustering", "cluster analysis", "кластеризац", "кластерный анализ"]):
        score += 3

    if _profile_title_matches(profile.title, title):
        score += 12
        reasons.append("совпадение с названием концепта")

    if profile.kind == "metric" and _contains_any(body, ["validation", "validity", "evaluation", "оценк", "качества"]):
        score += 4
    if profile.kind == "parameter" and _contains_any(body, ["parameter", "hyperparameter", "параметр"]):
        score += 4
    if profile.kind == "algorithm" and _contains_any(body, ["algorithm", "method", "алгоритм", "метод"]):
        score += 3

    score += min(math.log1p(max(article.citations, 0)), 5)

    year = _year_as_int(article.year)
    if year >= 2020:
        score += 2
    elif year >= 2015:
        score += 1

    if article.source == "Semantic Scholar":
        score += 1.5

    if not reasons and score > 0:
        reasons.append("общая тематическая близость")

    return score, reasons


def _matched_terms(text, terms):
    hits = []
    for term in terms:
        clean = _normalize(term)
        if len(clean) < 3:
            continue
        if clean in text:
            hits.append(term)
    return _dedupe(hits)


def _profile_title_matches(profile_title, title):
    clean_title = _normalize(profile_title)
    if len(clean_title) <= 3:
        return re.search(rf"\b{re.escape(clean_title)}\b", title) is not None
    return clean_title in title


def _contains_any(text, needles):
    return any(_normalize(needle) in text for needle in needles)


def _normalize(value):
    text = str(value or "").lower()
    text = text.replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _dedupe(values):
    seen = set()
    result = []
    for value in values:
        key = str(value).lower()
        if key not in seen:
            result.append(value)
            seen.add(key)
    return result


def _year_as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
