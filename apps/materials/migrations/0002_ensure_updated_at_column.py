from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("materials", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE core_material
                    ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone;

                    UPDATE core_material
                    SET updated_at = COALESCE(created_at, NOW())
                    WHERE updated_at IS NULL;

                    ALTER TABLE core_material
                    ALTER COLUMN updated_at SET NOT NULL;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
