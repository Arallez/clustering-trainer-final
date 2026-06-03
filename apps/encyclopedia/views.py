import json
import re
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from apps.tasks.models import UserTaskAttempt
from .models import Concept
from .article_service import get_recommended_articles_for_concept
from .curriculum import build_curriculum_modules
from .recommendations import (
    SOFT_RELATION_PRIORITY,
    get_all_required_concepts,
    get_learned_concepts,
    get_recommended_materials,
    get_recommended_tasks,
    get_user_progress,
)


def _concept_group(uri):
    """Определение группы узла по URI (для легенды графа)."""
    if not uri:
        return 9
    if 'Algo' in uri:
        return 1
    if 'Param' in uri:
        return 2
    if 'Metric' in uri or 'Distance' in uri:
        return 3
    if 'QMetric' in uri or 'QualityMetric' in uri:
        return 10
    if 'UC' in uri or 'UseCase' in uri:
        return 4
    if 'Geometry' in uri:
        return 5
    if 'Scalability' in uri:
        return 6
    if 'ClusterSize' in uri or 'Size' in uri:
        return 7
    if 'Inference' in uri or 'Inductive' in uri or 'Transductive' in uri:
        return 8
    if 'Criterion_' in uri or 'Condition_' in uri:
        return 11
    return 9


GRAPH_LATEX_REPLACEMENTS = {
    r"\epsilon": "ε",
    r"\varepsilon": "ε",
    r"\mu": "μ",
    r"\rho": "ρ",
    r"\ell": "ℓ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\sigma": "σ",
}


def _plain_graph_title(title):
    """Return a compact plain-text label for SVG graph nodes."""
    text = title or ""
    text = re.sub(r"\$\s*([^$]+?)\s*\$", r"\1", text)
    text = re.sub(r"\\\(\s*(.+?)\s*\\\)", r"\1", text)
    text = re.sub(r"\\\[\s*(.+?)\s*\\\]", r"\1", text)
    for latex, symbol in GRAPH_LATEX_REPLACEMENTS.items():
        text = text.replace(latex, symbol)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _get_cached_graph_data():
    """Получает кэшированные данные графа или строит их заново."""
    cache_key = 'ontology_graph_data_v2'
    data = cache.get(cache_key)
    
    if data is None:
        concepts = Concept.objects.prefetch_related('relations_out').all()
        
        nodes = []
        links = []
        for concept in concepts:
            nodes.append({
                'id': str(concept.id),
                'title': _plain_graph_title(concept.title),
                'raw_title': concept.title,
                'uri': concept.uri or '',
                'group': _concept_group(concept.uri),
                'url': reverse('encyclopedia:detail', kwargs={'pk': concept.id}),
                'desc': (concept.description or 'Нет описания')[:120],
            })
            for rel in concept.relations_out.all():
                links.append({
                    'source': str(concept.id),
                    'target': str(rel.target_id),
                    'type': rel.get_relation_type_display(),
                    'raw_type': rel.relation_type,
                })
        
        data = {'nodes': nodes, 'links': links}
        # Кэшируем на 5 минут
        cache.set(cache_key, data, timeout=300)
    
    return data


def graph_view(request):
    """Отображение графа знаний. Данные для графа передаются в JSON (островковая архитектура: HTML/CSS/JS отдельно)."""
    # Получаем кэшированные данные графа
    graph_data = _get_cached_graph_data()
    
    # Получаем ID изученных концептов, если пользователь авторизован
    learned_ids = set()
    if request.user.is_authenticated:
        learned_ids = set(get_learned_concepts(request.user).values_list('id', flat=True))
    
    # Добавляем флаг is_learned к узлам (это не кэшируется, т.к. зависит от пользователя)
    for node in graph_data['nodes']:
        node['is_learned'] = int(node['id']) in learned_ids
    
    graph_json = json.dumps(graph_data, ensure_ascii=False)
    
    return render(request, 'encyclopedia/graph.html', {
        'graph_data': graph_json,
        'is_authenticated': request.user.is_authenticated
    })

def concept_list(request):
    """Отображение списка всех понятий онтологии"""
    # Сортируем по названию для удобства
    concepts = Concept.objects.all().order_title() if hasattr(Concept.objects, 'order_title') else Concept.objects.all().order_by('title')
    return render(request, 'encyclopedia/list.html', {'concepts': concepts})

def concept_detail(request, pk):
    """Детальная страница понятия с отображением связей и рекомендаций"""
    concept = get_object_or_404(Concept, pk=pk)
    # Получаем входящие и исходящие связи
    relations_out = concept.relations_out.select_related('target')
    relations_in = concept.relations_in.select_related('source')
    
    # Задачи и материалы, привязанные к этому концепту
    related_tasks = concept.tasks.all() if hasattr(concept, 'tasks') else []
    related_materials = concept.materials.all() if hasattr(concept, 'materials') else []
    
    return render(request, 'encyclopedia/detail.html', {
        'concept': concept,
        'relations_out': relations_out,
        'relations_in': relations_in,
        'related_tasks': related_tasks,
        'related_materials': related_materials,
    })


def concept_articles_api(request, pk):
    """Return ontology-aware scientific article recommendations for a concept."""
    concept = get_object_or_404(
        Concept.objects.prefetch_related(
            "relations_out__target",
            "relations_in__source",
            "materials",
        ),
        pk=pk,
    )
    try:
        limit = min(max(int(request.GET.get("limit", 20)), 1), 40)
    except ValueError:
        limit = 20

    payload = get_recommended_articles_for_concept(concept, limit=limit)
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})


def _module_recommendation_rank(module):
    if module["status"] == "in_progress" or module["progress_percent"] > 0:
        band = 0
    elif module["status"] == "available":
        band = 1
    elif module["status"] == "planned":
        band = 3
    else:
        band = 4
    return band, module["order"]


def _get_recent_learning_signal(user, recent_limit=3):
    recent_attempts = (
        UserTaskAttempt.objects.filter(
            user=user,
            is_correct=True,
            task__concept__isnull=False,
        )
        .select_related("task__concept")
        .order_by("-created_at")
    )

    recent_concept_ids = []
    for attempt in recent_attempts:
        concept_id = attempt.task.concept_id
        if concept_id not in recent_concept_ids:
            recent_concept_ids.append(concept_id)
        if len(recent_concept_ids) >= recent_limit:
            break

    if not recent_concept_ids:
        return set(), set()

    followup_ids = set(
        Concept.objects.filter(
            relations_in__source_id__in=recent_concept_ids,
            relations_in__relation_type__in=list(SOFT_RELATION_PRIORITY.keys()),
        )
        .values_list("id", flat=True)
        .distinct()
    )

    return set(recent_concept_ids), followup_ids


def _task_matches_recent_learning(task, recent_concept_ids, recent_followup_ids):
    if not task.concept_id or not recent_concept_ids:
        return False
    if task.concept_id in recent_followup_ids:
        return True

    required_ids = {concept.id for concept in get_all_required_concepts(task.concept)}
    return bool(required_ids & recent_concept_ids)


def _get_adaptive_module_recommendations(user, learning_modules, task_limit=5, material_limit=5):
    solved_task_ids = set(
        UserTaskAttempt.objects.filter(user=user, is_correct=True).values_list("task_id", flat=True)
    )
    recent_concept_ids, recent_followup_ids = _get_recent_learning_signal(user)

    task_candidates = []
    for module in learning_modules:
        module_rank = _module_recommendation_rank(module)
        for task in module["available_tasks"]:
            if task.id in solved_task_ids:
                continue
            recent_rank = 0 if _task_matches_recent_learning(task, recent_concept_ids, recent_followup_ids) else 1
            task_candidates.append(
                (
                    recent_rank,
                    module_rank,
                    getattr(task, "order", 0),
                    getattr(task, "difficulty", 0),
                    task.title,
                    task,
                )
            )
    task_candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    material_candidates = []
    for module in learning_modules:
        module_rank = _module_recommendation_rank(module)
        for material in module["materials"]:
            if getattr(material, "is_completed", False):
                continue
            recent_rank = 0 if material.concept_id in recent_followup_ids else 1
            material_candidates.append((recent_rank, module_rank, getattr(material, "order", 0), material.title, material))
    material_candidates.sort(key=lambda item: (item[0], item[1], item[2]))

    return {
        "tasks": [item[-1] for item in task_candidates[:task_limit]],
        "materials": [item[-1] for item in material_candidates[:material_limit]],
    }

@login_required
def recommendations_view(request):
    """
    Страница адаптивного обучения.
    Показывает прогресс пользователя по онтологии и рекомендует следующие шаги.
    """
    # Получаем общую статистику
    progress_stats = get_user_progress(request.user)
    
    learning_modules = build_curriculum_modules(request.user)
    current_module = next((module for module in learning_modules if module["status"] == "in_progress"), None)
    if current_module is None:
        current_module = next((module for module in learning_modules if module["status"] == "available"), None)
    demo_module = current_module or next((module for module in learning_modules if module["slug"] == "module-1"), None)

    adaptive_recommendations = _get_adaptive_module_recommendations(request.user, learning_modules)
    recommended_tasks = adaptive_recommendations["tasks"]
    recommended_materials = adaptive_recommendations["materials"]

    if not recommended_tasks:
        recommended_tasks = get_recommended_tasks(request.user, limit=5)
    if not recommended_materials:
        recommended_materials = get_recommended_materials(request.user, limit=3)

    demo_final_task = None
    if demo_module:
        demo_final_task = next(
            (task for task in demo_module["tasks"] if task.slug == "quiz-module1-final-case"),
            None,
        )
    
    return render(request, 'encyclopedia/recommendations.html', {
        'progress': progress_stats,
        'recommended_tasks': recommended_tasks,
        'recommended_materials': recommended_materials,
        'learning_modules': learning_modules,
        'current_module': current_module,
        'demo_module': demo_module,
        'demo_final_task': demo_final_task,
    })
