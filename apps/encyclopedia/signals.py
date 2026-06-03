from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Concept, ConceptRelation


GRAPH_CACHE_KEY = 'ontology_graph_data'


def invalidate_graph_cache():
    """Инвалидирует кэш графа онтологии."""
    cache.delete(GRAPH_CACHE_KEY)


@receiver(post_save, sender=Concept)
@receiver(post_delete, sender=Concept)
def concept_changed(sender, **kwargs):
    """Срабатывает при создании, обновлении или удалении понятия."""
    invalidate_graph_cache()


@receiver(post_save, sender=ConceptRelation)
@receiver(post_delete, sender=ConceptRelation)
def relation_changed(sender, **kwargs):
    """Срабатывает при создании, обновлении или удалении связи."""
    invalidate_graph_cache()