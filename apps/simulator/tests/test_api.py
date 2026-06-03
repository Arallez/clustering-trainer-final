import json

from django.test import TestCase
from django.urls import reverse

from apps.simulator.presets import generate_preset


class SimulatorPresetTests(TestCase):
    def test_all_documented_presets_generate_points_inside_canvas(self):
        presets = [
            "moons",
            "circles",
            "blobs",
            "grid",
            "hierarchy",
            "dense_sparse",
            "anisotropic",
            "outliers",
            "many_blobs",
            "bridge",
        ]

        for preset in presets:
            with self.subTest(preset=preset):
                points = generate_preset(preset, n_samples=50)

                self.assertEqual(len(points), 50)
                self.assertTrue(
                    all(0 <= coordinate <= 10 for point in points for coordinate in point)
                )

    def test_preset_api_returns_default_simulator_dataset_size(self):
        response = self.client.get(reverse("simulator:get_preset"), {"name": "bridge"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["points"]), 300)


class SimulatorAlgorithmApiTests(TestCase):
    def test_kmeans_endpoint_returns_iteration_history(self):
        response = self.client.post(
            reverse("simulator:run_algorithm"),
            data=json.dumps(
                {
                    "algorithm": "kmeans",
                    "points": [[1, 1], [1.2, 1.1], [8, 8], [8.2, 8.1]],
                    "params": {"k": 2},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertGreater(len(payload["history"]), 0)

    def test_ward_dendrogram_endpoint_returns_plot_data(self):
        response = self.client.post(
            reverse("simulator:get_dendrogram"),
            data=json.dumps(
                {
                    "algorithm": "ward",
                    "points": [[1, 1], [1.1, 1.2], [8, 8], [8.2, 8.1]],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("icoord", payload["dendrogram"])
        self.assertIn("dcoord", payload["dendrogram"])

