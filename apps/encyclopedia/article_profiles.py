import re
from dataclasses import dataclass, field

from django.utils.html import strip_tags


STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "using", "based", "data",
    "algorithm", "metric", "index", "кластеризация", "кластеризации",
    "алгоритм", "метод", "метрика", "оценка", "данных", "параметр",
}


DOMAIN_ANCHORS_EN = [
    "clustering",
    "cluster analysis",
    "unsupervised learning",
    "machine learning",
    "data mining",
]

DOMAIN_ANCHORS_RU = [
    "кластеризация",
    "кластерный анализ",
    "обучение без учителя",
    "машинное обучение",
    "интеллектуальный анализ данных",
]


CONCEPT_SEARCH_OVERRIDES = {
    "optics": {
        "terms": ["OPTICS", "ordering points to identify clustering structure", "density-based clustering"],
        "negative": ["optical", "optics physics", "lens", "photon", "laser"],
        "query_en": "OPTICS clustering algorithm density-based",
        "query_ru": "OPTICS алгоритм кластеризация плотностная",
    },
    "birch": {
        "terms": ["BIRCH", "balanced iterative reducing and clustering using hierarchies", "CF tree"],
        "negative": ["birch tree", "forestry", "botany", "bark", "pollen"],
        "query_en": "BIRCH clustering algorithm CF tree",
        "query_ru": "BIRCH алгоритм кластеризация CF-дерево",
    },
    "dbscan": {
        "terms": ["DBSCAN", "density-based spatial clustering", "eps", "minPts", "noise"],
        "negative": [],
        "query_en": "DBSCAN density-based spatial clustering noise",
        "query_ru": "DBSCAN плотностная кластеризация шум",
    },
    "k-means": {
        "terms": ["k-means", "k means", "centroid-based clustering", "Lloyd algorithm"],
        "negative": [],
        "query_en": "k-means centroid-based clustering Lloyd algorithm",
        "query_ru": "k-means метод k средних кластеризация",
    },
    "kmeans": {
        "terms": ["k-means", "k means", "centroid-based clustering", "Lloyd algorithm"],
        "negative": [],
        "query_en": "k-means centroid-based clustering Lloyd algorithm",
        "query_ru": "k-means метод k средних кластеризация",
    },
    "mean-shift": {
        "terms": ["mean shift", "mode seeking", "kernel density estimation", "bandwidth"],
        "negative": [],
        "query_en": "mean shift clustering kernel density estimation bandwidth",
        "query_ru": "mean shift кластеризация оценка плотности ширина окна",
    },
    "gaussian": {
        "terms": ["Gaussian mixture model", "GMM", "model-based clustering", "EM algorithm"],
        "negative": [],
        "query_en": "Gaussian mixture model GMM model-based clustering EM",
        "query_ru": "гауссовы смеси GMM модельная кластеризация EM",
    },
    "silhouette": {
        "terms": ["silhouette score", "cluster validation", "internal validation index"],
        "negative": ["silhouette art", "image silhouette"],
        "query_en": "silhouette score clustering validation index",
        "query_ru": "силуэт оценка качества кластеризации",
    },
    "davies": {
        "terms": ["Davies-Bouldin index", "cluster validity index", "clustering evaluation"],
        "negative": [],
        "query_en": "Davies-Bouldin index clustering evaluation",
        "query_ru": "индекс Дэвиса Болдина оценка кластеризации",
    },
    "calinski": {
        "terms": ["Calinski-Harabasz index", "variance ratio criterion", "cluster validation"],
        "negative": [],
        "query_en": "Calinski-Harabasz index cluster validation",
        "query_ru": "индекс Калински Харабаса кластеризация",
    },
    "dunn": {
        "terms": ["Dunn index", "cluster validity index", "clustering evaluation"],
        "negative": ["Dunn disease", "Dunn test"],
        "query_en": "Dunn index clustering validation",
        "query_ru": "индекс Данна оценка кластеризации",
    },
    "rand": {
        "terms": ["Rand index", "adjusted rand index", "external cluster validation"],
        "negative": ["rand corporation", "rand function"],
        "query_en": "Rand index adjusted rand index clustering validation",
        "query_ru": "индекс Рэнда внешняя оценка кластеризации",
    },
}


@dataclass(frozen=True)
class ArticleSearchProfile:
    concept_id: int
    title: str
    kind: str
    query_en: str
    query_ru: str
    positive_terms: tuple[str, ...] = field(default_factory=tuple)
    context_terms: tuple[str, ...] = field(default_factory=tuple)
    negative_terms: tuple[str, ...] = field(default_factory=tuple)
    source_terms: tuple[str, ...] = field(default_factory=tuple)

    @property
    def cache_fingerprint(self):
        chunks = [
            str(self.concept_id),
            self.title,
            self.query_en,
            self.query_ru,
            "|".join(self.positive_terms),
            "|".join(self.negative_terms),
        ]
        return ":".join(_slugify(chunk) for chunk in chunks if chunk)


def build_article_search_profile(concept):
    """
    Build a domain-aware search profile from the ontology node and nearby content.

    The goal is to avoid querying external APIs by a short ambiguous title only.
    We enrich it with ontology type, descriptions, neighboring concepts and
    material titles, then rank articles against this richer profile.
    """
    title = _clean_text(concept.title)
    description = _clean_text(strip_tags(concept.description or ""))
    kind = _concept_kind(concept)

    neighbor_titles = _neighbor_titles(concept)
    material_titles = _material_titles(concept)
    source_terms = _extract_terms(" ".join([title, description, *neighbor_titles, *material_titles]))

    positive_terms = _ordered_unique([title, *_title_variants(title), *source_terms[:14]])
    negative_terms = []
    query_en = f"{title} clustering machine learning"
    query_ru = f"{title} кластеризация"

    for key, override in CONCEPT_SEARCH_OVERRIDES.items():
        probe = f"{title} {concept.uri or ''}".lower()
        if key in probe:
            positive_terms = _ordered_unique([*override["terms"], *positive_terms])
            negative_terms = _ordered_unique([*negative_terms, *override["negative"]])
            query_en = override["query_en"]
            query_ru = override["query_ru"]
            break

    if kind == "metric":
        positive_terms = _ordered_unique(["cluster validation", "clustering evaluation", *positive_terms])
        query_en = query_en if "validation" in query_en.lower() else f"{title} clustering validation index"
        query_ru = query_ru if "оцен" in query_ru.lower() else f"{title} оценка качества кластеризации"
    elif kind == "parameter":
        parent_terms = _ordered_unique(neighbor_titles[:4])
        positive_terms = _ordered_unique([*parent_terms, *positive_terms])
        query_en = f"{title} parameter clustering"
        query_ru = f"{title} параметр кластеризация"
    elif kind == "use_case":
        query_en = f"{title} clustering application"
        query_ru = f"{title} применение кластеризации"

    context_terms = _ordered_unique([*DOMAIN_ANCHORS_EN, *DOMAIN_ANCHORS_RU, *neighbor_titles[:8]])

    return ArticleSearchProfile(
        concept_id=concept.id,
        title=title,
        kind=kind,
        query_en=query_en,
        query_ru=query_ru,
        positive_terms=tuple(term.lower() for term in positive_terms if len(term) > 2),
        context_terms=tuple(term.lower() for term in context_terms if len(term) > 2),
        negative_terms=tuple(term.lower() for term in negative_terms if len(term) > 2),
        source_terms=tuple(source_terms),
    )


def _concept_kind(concept):
    uri = (concept.uri or "").lower()
    title = (concept.title or "").lower()
    if "algo" in uri:
        return "algorithm"
    if "param" in uri:
        return "parameter"
    if "qmetric" in uri or "qualitymetric" in uri or "metric" in uri or "index" in title or "индекс" in title:
        return "metric"
    if "usecase" in uri or "uc" in uri or "применение" in title:
        return "use_case"
    if "distance" in uri or "расстоя" in title:
        return "distance"
    return "concept"


def _neighbor_titles(concept):
    titles = []
    for relation in concept.relations_out.select_related("target").all()[:12]:
        titles.append(relation.target.title)
    for relation in concept.relations_in.select_related("source").all()[:12]:
        titles.append(relation.source.title)
    return [_clean_text(title) for title in titles if title]


def _material_titles(concept):
    if not hasattr(concept, "materials"):
        return []
    return [_clean_text(material.title) for material in concept.materials.all()[:8]]


def _extract_terms(text):
    text = _clean_text(text).lower()
    raw_terms = re.findall(r"[a-zа-яё][a-zа-яё0-9-]{3,}", text, flags=re.IGNORECASE)
    terms = []
    for term in raw_terms:
        if term in STOPWORDS:
            continue
        if len(term) < 4:
            continue
        terms.append(term)
    return _ordered_unique(terms)


def _title_variants(title):
    variants = []
    compact = title.replace("-", "").replace(" ", "")
    if compact and compact.lower() != title.lower():
        variants.append(compact)
    if "-" in title:
        variants.append(title.replace("-", " "))
    return variants


def _ordered_unique(values):
    seen = set()
    result = []
    for value in values:
        clean = _clean_text(value)
        key = clean.lower()
        if clean and key not in seen:
            result.append(clean)
            seen.add(key)
    return result


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _slugify(value):
    return re.sub(r"[^a-zа-яё0-9]+", "-", value.lower()).strip("-")[:80]
