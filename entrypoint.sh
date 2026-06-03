#!/bin/sh

echo "=== Waiting for database ==="
sleep 2

echo "=== Applying migrations ==="
python manage.py migrate --noinput

echo "=== Loading users ==="
if [ -f "fixtures/datadump.json" ]; then
    python manage.py loaddata fixtures/datadump.json
fi

echo "=== Syncing ontology concepts from OWL file ==="
python manage.py sync_ontology

echo "=== Loading course content (materials, tasks, modules) ==="
python manage.py load_test_course

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Starting server ==="
exec python manage.py runserver 0.0.0.0:8000
