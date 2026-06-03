from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("encyclopedia", "0005_course_modules"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coursemodulesimulator",
            name="algorithm",
            field=models.CharField(
                choices=[
                    ("kmeans", "K-Means"),
                    ("minibatch", "MiniBatch K-Means"),
                    ("bisecting", "Bisecting K-Means"),
                    ("dbscan", "DBSCAN"),
                    ("forel", "FOREL"),
                    ("optics", "OPTICS"),
                    ("meanshift", "Mean Shift"),
                    ("agglomerative", "Agglomerative Clustering"),
                    ("ward", "Ward"),
                    ("birch", "BIRCH"),
                    ("gmm", "Gaussian Mixture Models"),
                    ("spectral", "Spectral Clustering"),
                    ("affinity", "Affinity Propagation"),
                ],
                max_length=50,
                verbose_name="Алгоритм",
            ),
        ),
        migrations.AlterField(
            model_name="coursemodulesimulator",
            name="label",
            field=models.CharField(max_length=120, verbose_name="Название ссылки"),
        ),
        migrations.AlterField(
            model_name="coursemodulesimulator",
            name="preset",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Без стартового набора"),
                    ("blobs", "Облака"),
                    ("moons", "Луны"),
                    ("circles", "Кольца"),
                    ("grid", "Сетка"),
                    ("hierarchy", "Иерархия кластеров"),
                    ("dense_sparse", "Плотный и разреженный кластеры"),
                ],
                max_length=80,
                verbose_name="Стартовый набор данных",
            ),
        ),
    ]
