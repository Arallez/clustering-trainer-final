from pathlib import Path

from owlready2 import ThingClass, get_ontology, owl

from .models import Concept as DjangoConcept
from .models import ConceptRelation


# Жестко указываем использовать только нужный файл
ONTOLOGY_DIR = Path(__file__).resolve().parent / "data"
OWL_FILENAMES = ("clustering.owl",)


ROOT_CLUSTERING_DESCRIPTION = """Кластеризация — это задача анализа данных, в которой множество объектов разбивается на группы, называемые кластерами, без заранее заданных меток классов.

**Место в машинном обучении:**
Кластеризация относится к обучению без учителя. В отличие от классификации, алгоритм не получает готовые правильные ответы, а пытается обнаружить внутреннюю структуру данных по признакам объектов и выбранной мере сходства.

**Формальная постановка:**
Пусть задано множество объектов $X = \\{x_1, x_2, ..., x_n\\}$ и мера близости или расстояния $\\rho(x_i, x_j)$. Требуется построить разбиение:

$C = \\{C_1, C_2, ..., C_K\\}$,

такое, что каждый объект принадлежит одному из кластеров, кластеры не пересекаются, а их объединение образует исходную выборку. В общем виде хорошее разбиение должно обеспечивать два свойства:
1. объекты внутри одного кластера похожи друг на друга;
2. объекты из разных кластеров достаточно различаются.

**Критерии качества:**
Для центроидных методов, например K-Means, цель часто выражается через минимизацию внутрикластерной суммы квадратов:

$J = \\sum_{k=1}^{K} \\sum_{x_i \\in C_k} \\|x_i - \\mu_k\\|^2$,

где $\\mu_k$ — центр k-го кластера. Однако эта формула не является универсальной для всей кластеризации: плотностные, иерархические, графовые и модельные методы используют другие предположения о структуре данных.

**Роль в электронном пособии:**
В графе знаний это понятие используется как корневой узел. От него связываются основные группы методов кластеризации, метрики расстояния, параметры алгоритмов, критерии качества, условия применимости и практические сценарии. Такая организация помогает рассматривать кластеризацию не как набор отдельных алгоритмов, а как единую предметную область.

**Теоретическая опора:**
Описание понятия опирается на классические работы по кластерному анализу и машинному обучению: Б.Г. Миркина, К.В. Воронцова, A.K. Jain, M.N. Murty, P.J. Flynn, а также C.C. Aggarwal и C.K. Reddy."""


def sync_ontology():
    """
    Загружает OWL-файл и синхронизирует его с БД Django.
    Строит полное дерево с единым корнем "Кластеризация".
    """
    onto_path = None
    for filename in OWL_FILENAMES:
        path = ONTOLOGY_DIR / filename
        if path.exists():
            onto_path = path
            break

    if not onto_path:
        print("Файл онтологии не найден. Ожидается один из:")
        for fn in OWL_FILENAMES:
            print(f" - {fn}")
        return

    print(f"Загрузка онтологии из файла: {onto_path}")

    onto = get_ontology(f"file://{onto_path}")
    onto.load()

    classes_list = list(onto.classes())
    individuals_list = list(onto.individuals())
    print(f"Онтология загружена. Найдено классов: {len(classes_list)}, индивидов: {len(individuals_list)}")

    print("Синхронизация с базой данных...")

    def extract_name_from_uri(uri):
        if "#" in str(uri):
            return str(uri).split("#")[-1]
        if "/" in str(uri):
            return str(uri).split("/")[-1]
        return str(uri)

    def get_or_create_concept(owl_entity):
        entity_name = extract_name_from_uri(owl_entity.name)
        full_uri = entity_name

        title = entity_name
        if hasattr(owl_entity, "label") and owl_entity.label:
            labels = owl_entity.label if isinstance(owl_entity.label, list) else [owl_entity.label]
            for label in labels:
                if hasattr(label, "lang") and label.lang == "ru":
                    title = str(label)
                    break
            if title == entity_name and labels:
                title = str(labels[0])

        desc = ""
        if hasattr(owl_entity, "comment") and owl_entity.comment:
            comments = owl_entity.comment if isinstance(owl_entity.comment, list) else [owl_entity.comment]
            for comment in comments:
                if hasattr(comment, "lang") and comment.lang == "ru":
                    desc = str(comment)
                    break
            if not desc and comments:
                desc = str(comments[0])

        obj, created = DjangoConcept.objects.get_or_create(
            uri=full_uri,
            defaults={"title": title, "description": desc},
        )
        if not created:
            obj.title = title
            obj.description = desc
            obj.save()
        return obj

    property_mapping = {
        # Жёсткие связи — определяют доступность задач и эффективное освоение
        "hasPrerequisite": "DEPENDS",
        "usesMetric": "USES",
        "isExtensionOf": "EXTENDS",
        "isSpecialCaseOf": "SPECIAL_CASE",
        # Мягкие связи — управляют ранжированием рекомендаций
        "recommendedAfter": "RECOMMENDED_AFTER",
        "evaluatedBy": "EVALUATED_BY",
        # Структурные связи — сохраняют семантику предметной области
        "hasParameter": "HAS_PARAMETER",
        "solvesTask": "SOLVES_TASK",
        "supportsGeometry": "SUPPORTS_GEOMETRY",
        "assumesClusterSize": "ASSUMES_CLUSTER_SIZE",
        "hasScalability": "HAS_SCALABILITY",
        "hasInferenceType": "HAS_INFERENCE_TYPE",
        "assessesCriterion": "ASSESSES_CRITERION",
        "helpsSelectParameter": "HELPS_SELECT_PARAMETER",
    }

    root_concept, _ = DjangoConcept.objects.get_or_create(
        uri="Root_Clustering",
        defaults={
            "title": "Кластеризация",
            "description": ROOT_CLUSTERING_DESCRIPTION,
        },
    )
    if root_concept.title != "Кластеризация" or root_concept.description != ROOT_CLUSTERING_DESCRIPTION:
        root_concept.title = "Кластеризация"
        root_concept.description = ROOT_CLUSTERING_DESCRIPTION
        root_concept.save(update_fields=["title", "description"])

    print(f"Обработка {len(classes_list)} классов (иерархия IS_A)...")
    for cls in classes_list:
        if cls == owl.Thing:
            continue

        source_obj = get_or_create_concept(cls)
        has_real_parent = False

        for parent_cls in cls.is_a:
            if isinstance(parent_cls, ThingClass) and parent_cls != owl.Thing:
                has_real_parent = True
                target_obj = get_or_create_concept(parent_cls)
                ConceptRelation.objects.get_or_create(
                    source=source_obj,
                    target=target_obj,
                    relation_type="IS_A",
                )

        if not has_real_parent:
            ConceptRelation.objects.get_or_create(
                source=source_obj,
                target=root_concept,
                relation_type="IS_A",
            )

    print(f"Обработка {len(individuals_list)} индивидов...")
    for entity in individuals_list:
        source_obj = get_or_create_concept(entity)

        for parent_cls in entity.is_a:
            if isinstance(parent_cls, ThingClass) and parent_cls != owl.Thing:
                target_obj = get_or_create_concept(parent_cls)
                ConceptRelation.objects.get_or_create(
                    source=source_obj,
                    target=target_obj,
                    relation_type="IS_A",
                )

        for prop_name, relation_type in property_mapping.items():
            prop_value = None
            for attr_name in dir(entity):
                if attr_name.lower() == prop_name.lower():
                    prop_value = getattr(entity, attr_name, None)
                    break

            if not prop_value:
                continue

            target_entities = prop_value if isinstance(prop_value, list) else [prop_value]
            for target_entity in target_entities:
                if not target_entity:
                    continue
                target_obj = get_or_create_concept(target_entity)
                ConceptRelation.objects.get_or_create(
                    source=source_obj,
                    target=target_obj,
                    relation_type=relation_type,
                )

    print("База данных синхронизирована с онтологией.")
