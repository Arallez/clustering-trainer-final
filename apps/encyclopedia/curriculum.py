from django.urls import reverse

from apps.materials.models import Material, MaterialProgress
from apps.simulator.models import SimulatorProgress
from apps.tasks.models import Task, UserTaskAttempt

from .models import CourseModule
from .recommendations import build_learning_context, is_task_available


STATUS_META = {
    "available": {"label": "Можно проходить", "class_name": "status-available"},
    "in_progress": {"label": "В процессе", "class_name": "status-progress"},
    "completed": {"label": "Завершен", "class_name": "status-completed"},
    "planned": {"label": "Наполняется", "class_name": "status-planned"},
}


def _build_simulator_links(module, completed_simulator_keys=None):
    completed_simulator_keys = completed_simulator_keys or set()
    simulator_url = reverse("simulator:index")
    links = []

    for item in module.simulator_items.all():
        if not item.is_active:
            continue

        module_slug = item.get_progress_module_slug()
        url = f"{simulator_url}?algorithm={item.algorithm}"
        if item.preset:
            url = f"{url}&preset={item.preset}"
        if module_slug:
            url = f"{url}&module={module_slug}"

        progress_key = (module_slug, item.algorithm, item.preset or "")
        links.append(
            {
                "label": item.label,
                "url": url,
                "is_completed": progress_key in completed_simulator_keys,
            }
        )

    return links


def _get_module_tasks(module):
    query = Task.objects.none()
    task_tag_ids = list(module.task_tags.values_list("id", flat=True))
    task_ids = list(module.tasks.values_list("id", flat=True))
    concept_ids = list(module.concepts.values_list("id", flat=True))

    if task_tag_ids:
        query = query | Task.objects.filter(tags_id__in=task_tag_ids)
    if task_ids:
        query = query | Task.objects.filter(id__in=task_ids)
    if concept_ids:
        query = query | Task.objects.filter(concept_id__in=concept_ids)

    return query.select_related("concept", "tags").distinct().order_by("tags__order", "order", "title")


def _get_module_materials(module):
    query = Material.objects.none()
    material_ids = list(module.materials.values_list("id", flat=True))
    concept_ids = list(module.concepts.values_list("id", flat=True))

    if material_ids:
        query = query | Material.objects.filter(id__in=material_ids)
    if concept_ids:
        query = query | Material.objects.filter(concept_id__in=concept_ids)

    return query.select_related("concept").distinct().order_by("order", "title")


def _get_module_concepts(module):
    return module.concepts.all().order_by("title")


def _get_simulator_requirements(module):
    return [
        (item.get_progress_module_slug(), item.algorithm, item.preset or "")
        for item in module.simulator_items.all()
        if item.is_active
    ]


def _build_task_groups(tasks, concepts):
    groups = []
    grouped_concept_ids = set()
    tasks_by_concept_id = {}

    for task in tasks:
        tasks_by_concept_id.setdefault(task.concept_id, []).append(task)

    for concept in concepts:
        concept_tasks = tasks_by_concept_id.get(concept.id, [])
        if not concept_tasks:
            continue
        groups.append(
            {
                "title": concept.title,
                "uri": concept.uri,
                "description": concept.description,
                "tasks": concept_tasks,
                "tasks_count": len(concept_tasks),
                "quiz_count": sum(1 for task in concept_tasks if task.task_type == "choice"),
                "code_count": sum(1 for task in concept_tasks if task.task_type == "code"),
            }
        )
        grouped_concept_ids.add(concept.id)

    other_tasks = [task for task in tasks if task.concept_id not in grouped_concept_ids]
    if other_tasks:
        groups.append(
            {
                "title": "Дополнительная практика",
                "uri": "",
                "description": (
                    "Задачи, которые закрепляют модуль, но не привязаны к отдельному понятию онтологии."
                ),
                "tasks": other_tasks,
                "tasks_count": len(other_tasks),
                "quiz_count": sum(1 for task in other_tasks if task.task_type == "choice"),
                "code_count": sum(1 for task in other_tasks if task.task_type == "code"),
            }
        )

    return groups


def _get_course_modules():
    return (
        CourseModule.objects.filter(is_active=True)
        .prefetch_related(
            "concepts",
            "materials",
            "task_tags",
            "tasks",
            "prerequisites",
            "simulator_items",
        )
        .order_by("order", "title")
    )


def build_curriculum_modules(user=None):
    is_authenticated = bool(user and user.is_authenticated)
    learned_concept_ids = set()
    solved_task_ids = set()
    completed_material_ids = set()
    opened_material_ids = set()
    completed_simulator_keys = set()
    learning_context = None

    if is_authenticated:
        learning_context = build_learning_context(user)
        learned_concept_ids = set(learning_context.learned_ids)
        solved_task_ids = set(
            UserTaskAttempt.objects.filter(user=user, is_correct=True).values_list("task_id", flat=True)
        )
        completed_material_ids = set(
            MaterialProgress.objects.filter(
                user=user,
                completed_at__isnull=False,
            ).values_list("material_id", flat=True)
        )
        opened_material_ids = set(
            MaterialProgress.objects.filter(
                user=user,
                first_opened_at__isnull=False,
            ).values_list("material_id", flat=True)
        )
        completed_simulator_keys = set(
            SimulatorProgress.objects.filter(
                user=user,
                completed_at__isnull=False,
            ).values_list("module_slug", "algorithm", "preset")
        )

    modules = []

    for module in _get_course_modules():
        tasks = list(_get_module_tasks(module))
        materials = list(_get_module_materials(module))
        concepts = list(_get_module_concepts(module))
        simulator_requirements = _get_simulator_requirements(module)
        task_groups = _build_task_groups(tasks, concepts)

        available_tasks = []
        for task in tasks:
            if not is_authenticated:
                available_tasks.append(task)
                continue

            is_available, _ = is_task_available(user, task, context=learning_context)
            if is_available:
                available_tasks.append(task)

        solved_tasks = [task for task in tasks if task.id in solved_task_ids]
        learned_concepts = [concept for concept in concepts if concept.id in learned_concept_ids]
        completed_materials = [material for material in materials if material.id in completed_material_ids]

        for material in materials:
            material.is_completed = material.id in completed_material_ids
            material.is_opened = material.id in opened_material_ids

        task_progress = len(solved_tasks) / len(tasks) if tasks else 0
        concept_progress = len(learned_concepts) / len(concepts) if concepts else 0
        material_progress = len(completed_materials) / len(materials) if materials else 0
        completed_simulators_count = sum(1 for item in simulator_requirements if item in completed_simulator_keys)
        simulator_progress = completed_simulators_count / len(simulator_requirements) if simulator_requirements else 0

        if tasks and concepts and materials and simulator_requirements:
            progress_percent = int(
                (
                    (task_progress * 0.45)
                    + (concept_progress * 0.25)
                    + (material_progress * 0.2)
                    + (simulator_progress * 0.1)
                )
                * 100
            )
        elif tasks and concepts and materials:
            progress_percent = int(((task_progress * 0.5) + (concept_progress * 0.3) + (material_progress * 0.2)) * 100)
        elif tasks and concepts:
            progress_percent = int(((task_progress * 0.65) + (concept_progress * 0.35)) * 100)
        elif tasks and materials:
            progress_percent = int(((task_progress * 0.7) + (material_progress * 0.3)) * 100)
        elif concepts and materials:
            progress_percent = int(((concept_progress * 0.65) + (material_progress * 0.35)) * 100)
        elif tasks:
            progress_percent = int(task_progress * 100)
        elif materials:
            progress_percent = int(material_progress * 100)
        elif concepts:
            progress_percent = int(concept_progress * 100)
        else:
            progress_percent = 0

        has_learning_content = bool(tasks or materials or simulator_requirements)

        if not has_learning_content:
            status = "planned"
        elif (
            (not tasks or len(solved_tasks) == len(tasks))
            and (not concepts or len(learned_concepts) == len(concepts))
            and (not materials or len(completed_materials) == len(materials))
            and (not simulator_requirements or completed_simulators_count == len(simulator_requirements))
        ):
            status = "completed"
        elif progress_percent > 0:
            status = "in_progress"
        else:
            status = "available"

        recommended_tasks = [task for task in available_tasks if task.id not in solved_task_ids][:3]
        simulator_links = _build_simulator_links(module, completed_simulator_keys)

        next_actions = []
        if materials:
            next_actions.append("Изучить теорию и отметить материал как изученный")
        if simulator_links:
            next_actions.append("Пройти интерактивную симуляцию")
        if recommended_tasks:
            next_actions.append("Решить практические задачи")
        if not next_actions:
            next_actions.append("Модуль пока наполняется контентом")

        modules.append(
            {
                "id": module.id,
                "slug": module.slug,
                "order": module.order,
                "title": module.title,
                "subtitle": module.subtitle,
                "summary": module.summary,
                "highlights": module.get_highlights(),
                "prerequisites": list(module.prerequisites.all()),
                "status": status,
                "status_label": STATUS_META[status]["label"],
                "status_class": STATUS_META[status]["class_name"],
                "progress_percent": progress_percent,
                "tasks": tasks,
                "task_groups": task_groups,
                "materials": materials,
                "concepts": concepts[:6],
                "available_tasks": available_tasks,
                "recommended_tasks": recommended_tasks,
                "solved_tasks_count": len(solved_tasks),
                "tasks_count": len(tasks),
                "learned_concepts_count": len(learned_concepts),
                "concepts_count": len(concepts),
                "materials_count": len(materials),
                "completed_materials_count": len(completed_materials),
                "simulators_count": len(simulator_requirements),
                "completed_simulators_count": completed_simulators_count,
                "simulator_links": simulator_links,
                "next_actions": next_actions,
                "detail_url": f"{reverse('core:learning_path')}#{module.slug}",
            }
        )

    return modules


def get_current_curriculum_module(user=None):
    for module in build_curriculum_modules(user):
        if module["status"] in {"in_progress", "available"}:
            return module
    return None
