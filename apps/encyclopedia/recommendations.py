"""
Recommendation helpers for ontology-based adaptive learning.

The module separates two different kinds of educational logic:
- hard dependencies that gate access to a task;
- soft follow-up links that rank the next logical topic or task.
"""

from django.db.models import Count

from apps.materials.models import Material, MaterialProgress
from apps.simulator.models import SimulatorProgress
from apps.tasks.models import Task, UserTaskAttempt

from .models import Concept, ConceptRelation


HARD_RELATION_TYPES = ["DEPENDS", "USES", "EXTENDS", "SPECIAL_CASE"]
SOFT_RELATION_PRIORITY = {
    "RECOMMENDED_AFTER": 0,
    "EVALUATED_BY": 1,
}
CONCEPT_MASTERY_THRESHOLD = 0.8  # доля верно решённых задач для освоения концепта (mastery learning, 80–90%)


class LearningContext:
    """
    Request-sized cache for adaptive learning calculations.

    Task pages, profile and learning path need the same derived data many times:
    learned concepts, solved tasks and recursive ontology prerequisites. Building
    it once keeps the adaptive logic intact without issuing hundreds of repeated
    database queries during a single page render.
    """

    def __init__(self, user):
        self.user = user
        self.is_authenticated = bool(user and user.is_authenticated)
        self.task_totals = self._load_task_totals()
        self.solved_task_ids = self._load_solved_task_ids()
        self.solved_by_concept = self._load_solved_by_concept()
        self.hard_relation_map = self._load_hard_relation_map()
        self._required_cache = {}
        self.learned_ids = self._calculate_learned_ids()
        self.effective_learned_ids = self._calculate_effective_learned_ids()

    def _load_task_totals(self):
        return dict(
            Task.objects.filter(concept__isnull=False)
            .values("concept_id")
            .annotate(total=Count("id"))
            .values_list("concept_id", "total")
        )

    def _load_solved_task_ids(self):
        if not self.is_authenticated:
            return set()

        return set(
            UserTaskAttempt.objects.filter(
                user=self.user,
                is_correct=True,
            ).values_list("task_id", flat=True)
        )

    def _load_solved_by_concept(self):
        if not self.is_authenticated:
            return {}

        return dict(
            Task.objects.filter(
                concept__isnull=False,
                attempts__user=self.user,
                attempts__is_correct=True,
            )
            .values("concept_id")
            .annotate(solved=Count("id", distinct=True))
            .values_list("concept_id", "solved")
        )

    def _load_hard_relation_map(self):
        relation_map = {}
        for source_id, target_id in ConceptRelation.objects.filter(
            relation_type__in=HARD_RELATION_TYPES,
        ).values_list("source_id", "target_id"):
            relation_map.setdefault(source_id, set()).add(target_id)
        return relation_map

    def _calculate_learned_ids(self):
        learned_ids = set()
        for concept_id, total in self.task_totals.items():
            if total <= 0:
                continue

            solved = self.solved_by_concept.get(concept_id, 0)
            required = max(1, int((total * CONCEPT_MASTERY_THRESHOLD) + 0.999999))
            if solved >= required:
                learned_ids.add(concept_id)
        return learned_ids

    def _calculate_effective_learned_ids(self):
        learned_ids = set(self.learned_ids)
        for concept_id in self.learned_ids:
            learned_ids.update(self.get_all_required_concept_ids(concept_id))
        return learned_ids

    def get_mastery(self, concept):
        total = self.task_totals.get(concept.id, 0)
        if total == 0:
            return {
                "total": 0,
                "solved": 0,
                "required": 0,
                "ratio": 0,
                "is_learned": False,
            }

        solved = self.solved_by_concept.get(concept.id, 0)
        required = max(1, int((total * CONCEPT_MASTERY_THRESHOLD) + 0.999999))

        return {
            "total": total,
            "solved": solved,
            "required": required,
            "ratio": solved / total,
            "is_learned": solved >= required,
        }

    def get_all_required_concept_ids(self, concept_id, visited=None):
        if not concept_id:
            return set()
        if concept_id in self._required_cache:
            return set(self._required_cache[concept_id])
        if visited is None:
            visited = set()
        if concept_id in visited:
            return set()

        visited.add(concept_id)
        required_ids = set(self.hard_relation_map.get(concept_id, set()))
        for required_id in list(required_ids):
            required_ids.update(self.get_all_required_concept_ids(required_id, visited))

        self._required_cache[concept_id] = set(required_ids)
        return required_ids

    def is_task_available(self, task):
        if not task.concept_id:
            return True, []

        required_ids = self.get_all_required_concept_ids(task.concept_id)
        missing_ids = required_ids - self.effective_learned_ids
        return len(missing_ids) == 0, list(Concept.objects.filter(id__in=missing_ids))


def build_learning_context(user):
    return LearningContext(user)


def get_concept_mastery(user, concept, context=None):
    """
    Return mastery information for a primary ontology concept.

    Only tasks where the concept is primary are counted. Related concepts are
    diagnostic hints, not direct evidence of mastery.
    """
    context = context or build_learning_context(user)
    return context.get_mastery(concept)


def get_learned_concepts(user, context=None):
    """
    Return ontology concepts whose primary tasks are mastered by the user.
    """
    context = context or build_learning_context(user)
    return Concept.objects.filter(id__in=context.learned_ids).distinct()


def get_effective_learned_concept_ids(user, context=None):
    """
    Return concept IDs that can be treated as covered for task availability.

    A correctly solved advanced task is also evidence that the learner can use
    its hard prerequisites. This keeps the route adaptive when a student jumps
    ahead and demonstrates knowledge from a later module.
    """
    context = context or build_learning_context(user)
    return set(context.effective_learned_ids)


def get_required_concepts(concept):
    """
    Return concepts required to study the given concept.
    """
    return Concept.objects.filter(
        relations_in__source=concept,
        relations_in__relation_type__in=HARD_RELATION_TYPES,
    ).distinct()


def get_all_required_concepts(concept, visited=None, context=None):
    """
    Recursively resolve all hard prerequisites for a concept.
    """
    if context is not None:
        return set(Concept.objects.filter(id__in=context.get_all_required_concept_ids(concept.id)))

    context = build_learning_context(None)
    return set(Concept.objects.filter(id__in=context.get_all_required_concept_ids(concept.id)))


def get_followup_concepts(user, context=None):
    """
    Return concepts that are logical next steps after the already learned ones.

    RECOMMENDED_AFTER is a soft pedagogical transition.
    EVALUATED_BY is a softer analytical follow-up, for example when a student
    should next study how to assess the algorithm they have just learned.
    """
    context = context or build_learning_context(user)
    return Concept.objects.filter(
        relations_in__source_id__in=context.learned_ids,
        relations_in__relation_type__in=list(SOFT_RELATION_PRIORITY.keys()),
    ).distinct()


def get_followup_concept_ids_by_type(user, relation_type, context=None):
    """
    Return follow-up concept IDs for a specific soft relation type.
    """
    context = context or build_learning_context(user)
    return set(
        Concept.objects.filter(
            relations_in__source_id__in=context.learned_ids,
            relations_in__relation_type=relation_type,
        )
        .values_list("id", flat=True)
        .distinct()
    )


def is_task_available(user, task, context=None):
    """
    Check whether the task is available for the user.
    A task is available when all hard prerequisites of its concept are learned.
    """
    context = context or build_learning_context(user)
    return context.is_task_available(task)


def get_recommended_tasks(user, limit=10):
    """
    Return tasks that the user can already solve.
    Soft transitions are used only for ranking, not for blocking access.
    """
    context = build_learning_context(user)
    available_tasks = []
    recommended_after_ids = get_followup_concept_ids_by_type(user, "RECOMMENDED_AFTER", context=context)
    evaluated_by_ids = get_followup_concept_ids_by_type(user, "EVALUATED_BY", context=context)

    for task in Task.objects.filter(concept__isnull=False).select_related("concept"):
        is_available, _ = is_task_available(user, task, context=context)
        if not is_available:
            continue

        if task.id not in context.solved_task_ids:
            available_tasks.append(task)

    available_tasks.sort(
        key=lambda task: (
            0
            if task.concept_id in recommended_after_ids
            else 1
            if task.concept_id in evaluated_by_ids
            else 2,
            getattr(task, "difficulty", 0),
            getattr(task, "order", 0),
        )
    )

    return available_tasks[:limit]


def get_recommended_materials(user, limit=5):
    """
    Return materials for missing prerequisites and for the next logical topics.
    """
    context = build_learning_context(user)
    completed_material_ids = set(
        MaterialProgress.objects.filter(
            user=user,
            completed_at__isnull=False,
        ).values_list("material_id", flat=True)
    )

    learned_ids = set(context.learned_ids)
    recommended_after_ids = get_followup_concept_ids_by_type(user, "RECOMMENDED_AFTER", context=context)
    evaluated_by_ids = get_followup_concept_ids_by_type(user, "EVALUATED_BY", context=context)

    all_required_ids = set()
    for concept_id in Task.objects.filter(concept__isnull=False).values_list("concept_id", flat=True).distinct():
        all_required_ids.update(context.get_all_required_concept_ids(concept_id))

    missing_concept_ids = all_required_ids - learned_ids
    followup_concept_ids = set(get_followup_concepts(user, context=context).values_list("id", flat=True))
    candidate_concept_ids = missing_concept_ids | followup_concept_ids

    material_candidates = list(
        Material.objects.filter(
            concept_id__in=candidate_concept_ids,
        )
        .exclude(id__in=completed_material_ids)
        .distinct()
        .select_related("concept")
    )

    material_candidates.sort(
        key=lambda material: (
            0
            if material.concept_id in recommended_after_ids
            else 1
            if material.concept_id in evaluated_by_ids
            else 2,
            0 if material.concept_id in missing_concept_ids else 1,
            getattr(material, "order", 0),
            material.title,
        )
    )

    return material_candidates[:limit]


def get_task_remediation(user, task, limit=5):
    """
    Suggest concepts and materials to repeat after an incorrect attempt.

    The primary concept is shown first; related concepts are used as possible
    sources of the error.
    """
    context = build_learning_context(user)
    concept_ids = []
    if task.concept_id:
        concept_ids.append(task.concept_id)
    concept_ids.extend(task.related_concepts.values_list("id", flat=True))

    ordered_ids = []
    for concept_id in concept_ids:
        if concept_id not in ordered_ids:
            ordered_ids.append(concept_id)

    concepts = list(Concept.objects.filter(id__in=ordered_ids))
    concepts.sort(key=lambda concept: ordered_ids.index(concept.id))

    materials = list(
        Material.objects.filter(concept_id__in=ordered_ids)
        .select_related("concept")
        .order_by("order", "title")[:limit]
    )

    return {
        "concepts": [
            {
                "title": concept.title,
                "uri": concept.uri,
                "role": "primary" if concept.id == task.concept_id else "related",
                "mastery": get_concept_mastery(user, concept, context=context) if user.is_authenticated else None,
            }
            for concept in concepts
        ],
        "materials": [
            {
                "title": material.title,
                "url": material.get_absolute_url(),
                "concept": material.concept.title if material.concept else "",
            }
            for material in materials
        ],
    }


def get_learning_path(user, target_concept):
    """
    Return a learning path from the current user level to the target concept.
    """
    context = build_learning_context(user)
    learned_ids = set(context.learned_ids)
    required_concepts = get_all_required_concepts(target_concept, context=context)

    missing_concepts = [concept for concept in required_concepts if concept.id not in learned_ids]
    if target_concept.id not in learned_ids:
        missing_concepts.append(target_concept)

    def dependency_count(concept):
        return len(context.get_all_required_concept_ids(concept.id))

    missing_concepts.sort(key=dependency_count)

    path_tasks = {}
    path_materials = {}
    for concept in missing_concepts:
        path_tasks[concept] = Task.objects.filter(concept=concept)
        path_materials[concept] = Material.objects.filter(concept=concept)

    return {
        "path": missing_concepts,
        "tasks": path_tasks,
        "materials": path_materials,
    }


def get_user_progress(user):
    """
    Return user progress statistics across the ontology.
    """
    context = build_learning_context(user)
    learned_count = len(context.learned_ids)
    total_concepts = Concept.objects.count()
    completed_materials_count = MaterialProgress.objects.filter(
        user=user,
        completed_at__isnull=False,
    ).count()
    total_materials = Material.objects.count()
    completed_simulators_count = SimulatorProgress.objects.filter(
        user=user,
        completed_at__isnull=False,
    ).count()

    available_count = 0
    blocked_count = 0

    for task in Task.objects.filter(concept__isnull=False).select_related("concept"):
        is_available, _ = is_task_available(user, task, context=context)
        if is_available:
            if task.id not in context.solved_task_ids:
                available_count += 1
        else:
            blocked_count += 1

    progress_percent = int((learned_count / total_concepts * 100)) if total_concepts > 0 else 0

    return {
        "learned_count": learned_count,
        "total_count": total_concepts,
        "progress_percent": progress_percent,
        "available_tasks_count": available_count,
        "blocked_tasks_count": blocked_count,
        "completed_materials_count": completed_materials_count,
        "total_materials_count": total_materials,
        "completed_simulators_count": completed_simulators_count,
    }
