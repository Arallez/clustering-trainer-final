"""
Django management command for syncing the active OWL ontology with the database.

Usage:
    python manage.py sync_ontology
    python manage.py sync_ontology --clear
"""
from django.core.management.base import BaseCommand

from apps.encyclopedia.models import Concept
from apps.encyclopedia.ontology import sync_ontology


class Command(BaseCommand):
    help = 'Synchronizes apps/encyclopedia/data/clustering.owl with Django models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing Concept rows before reloading the ontology',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Deleting current ontology data from the database...'))
            Concept.objects.all().delete()
            self.stdout.write('Existing ontology data deleted.')

        self.stdout.write(self.style.SUCCESS('Starting ontology synchronization...'))

        try:
            sync_ontology()
            self.stdout.write(self.style.SUCCESS('Ontology synchronization completed successfully.'))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Ontology synchronization failed: {exc}'))
            raise
