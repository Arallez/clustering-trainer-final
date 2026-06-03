import os
import sys
from pathlib import Path

import django
from django.core.management import call_command


BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = BASE_DIR / "fixtures"
DUMP_PATH = FIXTURES_DIR / "datadump.json"

sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

FIXTURES_DIR.mkdir(exist_ok=True)

with DUMP_PATH.open("w", encoding="utf-8") as output:
    call_command(
        "dumpdata",
        natural_foreign=True,
        natural_primary=True,
        exclude=["contenttypes", "auth.Permission", "admin", "sessions"],
        indent=4,
        stdout=output,
    )

print(f"Fixture dump written to {DUMP_PATH}")
