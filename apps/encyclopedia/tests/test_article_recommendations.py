from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from apps.encyclopedia.article_profiles import build_article_search_profile
from apps.encyclopedia.article_ranker import rank_articles
from apps.encyclopedia.article_sources import ScientificArticle
from apps.encyclopedia.models import Concept


class ArticleRecommendationTests(TestCase):
    def test_profile_adds_disambiguation_for_birch(self):
        concept = Concept.objects.create(
            uri="Algo_BIRCH",
            title="BIRCH",
            description="Иерархический алгоритм кластеризации на основе CF-дерева.",
        )

        profile = build_article_search_profile(concept)

        self.assertIn("cf tree", profile.query_en.lower())
        self.assertIn("birch tree", profile.negative_terms)

    def test_ranker_prefers_clustering_article_over_ambiguous_context(self):
        concept = Concept.objects.create(uri="Algo_BIRCH", title="BIRCH")
        profile = build_article_search_profile(concept)
        articles = [
            ScientificArticle(
                id="bad",
                title="Birch tree pollen distribution in northern forests",
                authors="A. Botanist",
                year="2024",
                abstract="A botany study about forestry, bark and pollen.",
                url="#",
                pdf_url=None,
                citations=100,
                language="en",
                source="Crossref",
            ),
            ScientificArticle(
                id="good",
                title="BIRCH clustering algorithm with improved CF tree construction",
                authors="T. Zhang",
                year="2022",
                abstract="The paper studies hierarchical clustering and cluster analysis for large datasets.",
                url="#",
                pdf_url=None,
                citations=10,
                language="en",
                source="Semantic Scholar",
            ),
        ]

        ranked = rank_articles(profile, articles, limit=5)

        self.assertEqual(ranked[0]["id"], "good")
        self.assertNotIn("bad", [article["id"] for article in ranked])

    @patch("apps.encyclopedia.article_service.fetch_articles_for_profile")
    def test_concept_articles_api_returns_ranked_payload(self, fetch_articles_for_profile):
        concept = Concept.objects.create(uri="Algo_DBSCAN", title="DBSCAN")
        fetch_articles_for_profile.return_value = [
            ScientificArticle(
                id="dbscan-paper",
                title="DBSCAN density-based spatial clustering revisited",
                authors="M. Ester",
                year="2021",
                abstract="Density-based clustering discovers clusters and noise in spatial data.",
                url="https://example.test/dbscan",
                pdf_url=None,
                citations=42,
                language="en",
                source="Semantic Scholar",
            )
        ]

        response = self.client.get(reverse("encyclopedia:concept_articles_api", args=[concept.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["concept"]["title"], "DBSCAN")
        self.assertEqual(payload["articles"][0]["id"], "dbscan-paper")
        self.assertGreater(payload["articles"][0]["relevanceScore"], 0)
