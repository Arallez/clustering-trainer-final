from django.contrib.auth.models import User
from django.test import TestCase

from apps.encyclopedia.models import Concept, ConceptRelation
from apps.encyclopedia.recommendations import (
    get_concept_mastery,
    get_task_remediation,
    is_task_available,
)
from apps.materials.models import Material
from apps.tasks.models import Task, UserTaskAttempt


class AdaptiveRecommendationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="pass")

    def test_concept_mastery_requires_eighty_percent_of_primary_tasks(self):
        concept = Concept.objects.create(uri="concept:kmeans", title="K-Means")
        first_task = Task.objects.create(
            title="Task 1",
            slug="task-1",
            description="",
            concept=concept,
        )
        Task.objects.create(
            title="Task 2",
            slug="task-2",
            description="",
            concept=concept,
        )
        UserTaskAttempt.objects.create(
            user=self.user,
            task=first_task,
            code="answer",
            is_correct=True,
        )

        mastery = get_concept_mastery(self.user, concept)

        self.assertEqual(mastery["total"], 2)
        self.assertEqual(mastery["solved"], 1)
        self.assertEqual(mastery["required"], 2)
        self.assertFalse(mastery["is_learned"])

    def test_task_availability_uses_hard_ontology_dependencies(self):
        prerequisite = Concept.objects.create(uri="concept:distance", title="Distance")
        advanced = Concept.objects.create(uri="concept:dbscan", title="DBSCAN")
        ConceptRelation.objects.create(
            source=advanced,
            target=prerequisite,
            relation_type="DEPENDS",
        )
        task = Task.objects.create(
            title="DBSCAN task",
            slug="dbscan-task",
            description="",
            concept=advanced,
        )

        is_available, missing = is_task_available(self.user, task)

        self.assertFalse(is_available)
        self.assertEqual([concept.title for concept in missing], ["Distance"])

    def test_task_remediation_includes_primary_and_related_concepts(self):
        primary = Concept.objects.create(uri="concept:gmm", title="GMM")
        related = Concept.objects.create(uri="concept:em", title="EM")
        Material.objects.create(
            title="GMM theory",
            slug="gmm-theory",
            content="",
            concept=primary,
        )
        Material.objects.create(
            title="EM theory",
            slug="em-theory",
            content="",
            concept=related,
        )
        task = Task.objects.create(
            title="GMM task",
            slug="gmm-task",
            description="",
            concept=primary,
        )
        task.related_concepts.add(related)

        remediation = get_task_remediation(self.user, task)

        self.assertEqual(
            [(item["title"], item["role"]) for item in remediation["concepts"]],
            [("GMM", "primary"), ("EM", "related")],
        )
        self.assertEqual(
            [item["title"] for item in remediation["materials"]],
            ["EM theory", "GMM theory"],
        )

