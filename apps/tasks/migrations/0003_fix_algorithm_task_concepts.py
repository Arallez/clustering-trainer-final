from django.db import migrations


FORWARD_MAP = {
    'test-code-kmeans': 'Algo_KMeans',
}

REVERSE_MAP = {
    'test-code-kmeans': 'Algo_BisectingKMeans',
}


def _apply_mapping(apps, slug_to_uri):
    Task = apps.get_model('tasks', 'Task')
    Concept = apps.get_model('encyclopedia', 'Concept')

    for slug, uri in slug_to_uri.items():
        task = Task.objects.filter(slug=slug).first()
        concept = Concept.objects.filter(uri=uri).first()
        if task is None or concept is None:
            continue
        task.concept_id = concept.pk
        task.save(update_fields=['concept'])


def forwards(apps, schema_editor):
    _apply_mapping(apps, FORWARD_MAP)


def backwards(apps, schema_editor):
    _apply_mapping(apps, REVERSE_MAP)


class Migration(migrations.Migration):

    dependencies = [
        ('encyclopedia', '0004_alter_conceptrelation_relation_type_add_recommended_after'),
        ('tasks', '0002_task_concept'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
