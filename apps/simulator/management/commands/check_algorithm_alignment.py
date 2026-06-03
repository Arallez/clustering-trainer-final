from django.core.management.base import BaseCommand, CommandError

from apps.encyclopedia.models import Concept
from apps.simulator.catalog import (
    ONTOLOGY_ONLY_ALGORITHMS,
    SIMULATOR_ALGORITHM_CONCEPT_MAP,
    TASK_CONCEPT_EXPECTATIONS,
)
from apps.tasks.models import Task


class Command(BaseCommand):
    help = 'Checks consistency between simulator algorithms, ontology concepts, and task mappings.'

    def handle(self, *args, **options):
        ontology_algorithms = set(
            Concept.objects.filter(uri__startswith='Algo_').values_list('uri', flat=True)
        )
        simulator_algorithms = set(SIMULATOR_ALGORITHM_CONCEPT_MAP.values())

        unexpected_missing = sorted(ontology_algorithms - simulator_algorithms - ONTOLOGY_ONLY_ALGORITHMS)
        missing_in_ontology = sorted(simulator_algorithms - ontology_algorithms)

        task_errors = []
        for slug, expected_uri in TASK_CONCEPT_EXPECTATIONS.items():
            task = Task.objects.filter(slug=slug).select_related('concept').first()
            if task is None:
                task_errors.append(f'Missing task: {slug}')
                continue
            if task.concept is None:
                task_errors.append(f'Task {slug} has no ontology concept')
                continue
            if task.concept.uri != expected_uri:
                task_errors.append(
                    f'Task {slug} points to {task.concept.uri}, expected {expected_uri}'
                )

        if unexpected_missing:
            self.stdout.write(self.style.WARNING('Ontology concepts without simulator coverage:'))
            for uri in unexpected_missing:
                self.stdout.write(f'  - {uri}')

        if ONTOLOGY_ONLY_ALGORITHMS:
            self.stdout.write('Known ontology-only concepts:')
            for uri in sorted(ONTOLOGY_ONLY_ALGORITHMS):
                self.stdout.write(f'  - {uri}')

        if missing_in_ontology:
            self.stdout.write(self.style.ERROR('Simulator concepts missing in ontology:'))
            for uri in missing_in_ontology:
                self.stdout.write(f'  - {uri}')

        if task_errors:
            self.stdout.write(self.style.ERROR('Task mapping issues:'))
            for error in task_errors:
                self.stdout.write(f'  - {error}')

        if unexpected_missing or missing_in_ontology or task_errors:
            raise CommandError('Algorithm alignment check failed.')

        self.stdout.write(
            self.style.SUCCESS(
                f'Algorithm alignment is valid: {len(simulator_algorithms)} simulator algorithms, '
                f'{len(ontology_algorithms)} ontology algorithm concepts.'
            )
        )
