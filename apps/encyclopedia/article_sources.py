import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass


SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_API_URL = "https://api.crossref.org/works"
HTTP_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class ScientificArticle:
    id: str
    title: str
    authors: str
    year: str
    abstract: str
    url: str
    pdf_url: str | None
    citations: int
    language: str
    source: str
    doi: str = ""

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "url": self.url,
            "pdfUrl": self.pdf_url,
            "citations": self.citations,
            "language": self.language,
            "source": self.source,
            "doi": self.doi,
        }


def fetch_articles_for_profile(profile, per_source_limit=30):
    articles = []
    articles.extend(fetch_semantic_scholar(profile.query_en, per_source_limit))
    articles.extend(fetch_crossref(profile.query_en, per_source_limit, language="en", title_only=True))
    articles.extend(fetch_crossref(profile.query_ru, per_source_limit, language="ru", title_only=False))
    return deduplicate_articles(articles)


def fetch_semantic_scholar(query, limit=30):
    params = {
        "query": query,
        "limit": str(limit),
        "fields": "title,authors,year,url,abstract,citationCount,openAccessPdf",
    }
    url = f"{SEMANTIC_SCHOLAR_API_URL}?{urllib.parse.urlencode(params)}"
    data = _load_json(url)
    items = data.get("data") or []
    articles = []

    for item in items:
        title = _first_text(item.get("title"))
        if not title:
            continue
        authors = item.get("authors") or []
        articles.append(
            ScientificArticle(
                id=f"s2_{item.get('paperId') or _stable_text_id(title)}",
                title=title,
                authors=_format_s2_authors(authors),
                year=str(item.get("year") or "N/A"),
                abstract=_shorten(item.get("abstract") or ""),
                url=item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId')}",
                pdf_url=(item.get("openAccessPdf") or {}).get("url"),
                citations=int(item.get("citationCount") or 0),
                language="en",
                source="Semantic Scholar",
            )
        )
    return articles


def fetch_crossref(query, limit=30, language="en", title_only=False):
    query_key = "query.title" if title_only else "query"
    params = {
        query_key: query,
        "select": "title,author,URL,abstract,is-referenced-by-count,published,DOI",
        "filter": "type:journal-article",
        "rows": str(limit),
    }
    url = f"{CROSSREF_API_URL}?{urllib.parse.urlencode(params)}"
    data = _load_json(url)
    items = (data.get("message") or {}).get("items") or []
    articles = []

    for item in items:
        title = _first_text(item.get("title"))
        if not title:
            continue

        has_cyrillic = bool(re.search(r"[А-Яа-яЁё]", title))
        if language == "ru" and not has_cyrillic:
            continue
        if language == "en" and has_cyrillic:
            continue

        doi = item.get("DOI") or ""
        articles.append(
            ScientificArticle(
                id=f"cr_{doi or _stable_text_id(title)}",
                title=title,
                authors=_format_crossref_authors(item.get("author") or [], language),
                year=_crossref_year(item),
                abstract=_shorten(_strip_html(item.get("abstract") or "")),
                url=item.get("URL") or (f"https://doi.org/{doi}" if doi else "#"),
                pdf_url=None,
                citations=int(item.get("is-referenced-by-count") or 0),
                language=language,
                source="Crossref",
                doi=doi,
            )
        )
    return articles


def deduplicate_articles(articles):
    seen = set()
    result = []
    for article in articles:
        key = article.doi.lower().strip() if article.doi else _stable_text_id(article.title)
        if key in seen:
            continue
        seen.add(key)
        result.append(article)
    return result


def _load_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "diploma-clustering-app/1.0 (mailto:student@example.local)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            if response.status >= 400:
                return {}
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}


def _format_s2_authors(authors):
    names = [author.get("name", "").strip() for author in authors if author.get("name")]
    return _format_names(names, "Unknown Author")


def _format_crossref_authors(authors, language):
    names = []
    for author in authors:
        name = " ".join(part for part in [author.get("given"), author.get("family")] if part).strip()
        if name:
            names.append(name)
    fallback = "Неизвестный автор" if language == "ru" else "Unknown Author"
    return _format_names(names, fallback)


def _format_names(names, fallback):
    if not names:
        return fallback
    if len(names) <= 3:
        return ", ".join(names)
    return f"{names[0]}, {names[1]} et al."


def _crossref_year(item):
    date_parts = (item.get("published") or {}).get("date-parts") or []
    if date_parts and date_parts[0]:
        return str(date_parts[0][0])
    return "N/A"


def _first_text(value):
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value or "").strip()


def _strip_html(value):
    return re.sub(r"<[^>]*>", "", value)


def _shorten(value, limit=420):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _stable_text_id(value):
    return re.sub(r"[^a-zа-яё0-9]+", "-", value.lower()).strip("-")[:120]
