-- Пометить миграции как применённые (если нужно).
-- Из корня проекта: sqlite3 db.sqlite3 < scripts/fix_migrations.sql

INSERT OR IGNORE INTO django_migrations (app, name, applied) 
VALUES ('core', '0003_alter_material_tags_to_tasks', datetime('now'));

INSERT OR IGNORE INTO django_migrations (app, name, applied) 
VALUES ('testing', '0002_alter_test_tasks_to_tasks', datetime('now'));
