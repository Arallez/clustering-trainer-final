from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('materials', '0001_initial'),
        ('core', '0006_materialprogress'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='MaterialProgress'),
                migrations.DeleteModel(name='Material'),
            ],
        ),
    ]
