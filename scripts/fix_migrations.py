"""
Пометить core.0003 и testing.0002 как применённые в django_migrations.
Запуск из корня проекта: python scripts/fix_migrations.py
После этого: python manage.py migrate
"""
import sqlite3
import os

_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(_base, 'db.sqlite3')
if not os.path.exists(db_path):
    print('Файл db.sqlite3 не найден. Запустите скрипт из корня: python scripts/fix_migrations.py')
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    cur.execute(
        "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES (?, ?, datetime('now'))",
        ('core', '0003_alter_material_tags_to_tasks')
    )
    cur.execute(
        "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES (?, ?, datetime('now'))",
        ('testing', '0002_alter_test_tasks_to_tasks')
    )
    conn.commit()
    print('Записи добавлены в django_migrations. Теперь выполните: python manage.py migrate')
except Exception as e:
    print('Ошибка:', e)
    conn.rollback()
finally:
    conn.close()
