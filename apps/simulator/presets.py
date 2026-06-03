"""Dataset preset generators for clustering algorithms"""
import numpy as np
from sklearn.datasets import make_moons, make_circles, make_blobs


def _split_counts(n_samples, fractions):
    counts = [int(n_samples * fraction) for fraction in fractions]
    counts[-1] += n_samples - sum(counts)
    return counts


def generate_preset(preset_type: str, n_samples: int = 100):
    """
    Generate predefined datasets for clustering visualization.
    
    Args:
        preset_type: 'moons', 'circles', 'blobs', 'grid', 'hierarchy',
            'dense_sparse', 'anisotropic', 'outliers', 'many_blobs', 'bridge'
        n_samples: Number of points to generate
    
    Returns:
        List of [x, y] coordinates scaled to [0, 10] range
    """
    if preset_type == 'moons':
        X, _ = make_moons(n_samples=n_samples, noise=0.08, random_state=42)
    elif preset_type == 'circles':
        X, _ = make_circles(n_samples=n_samples, noise=0.05, factor=0.5, random_state=42)
    elif preset_type == 'blobs':
        X, _ = make_blobs(n_samples=n_samples, centers=3, cluster_std=0.6, random_state=42)
    elif preset_type == 'grid':
        # Custom grid pattern
        side = int(np.ceil(np.sqrt(n_samples)))
        x = np.linspace(0, 1, side)
        y = np.linspace(0, 1, side)
        xx, yy = np.meshgrid(x, y)
        X = np.column_stack([xx.ravel(), yy.ravel()])[:n_samples]
    elif preset_type == 'hierarchy':
        # Two large super-clusters, each containing 2 smaller clusters
        # Group 1
        X1, _ = make_blobs(n_samples=n_samples // 2, centers=[(0,0), (2,2)], cluster_std=0.4, random_state=1)
        # Group 2 (far away)
        X2, _ = make_blobs(n_samples=n_samples // 2, centers=[(8,8), (10,6)], cluster_std=0.4, random_state=2)
        X = np.vstack([X1, X2])
    elif preset_type == 'dense_sparse':
        # One very dense cluster and one sparse cluster
        X1, _ = make_blobs(n_samples=int(n_samples * 0.7), centers=[(0,0)], cluster_std=0.3, random_state=1)
        X2, _ = make_blobs(n_samples=int(n_samples * 0.3), centers=[(5,5)], cluster_std=1.5, random_state=2)
        X = np.vstack([X1, X2])
    elif preset_type == 'anisotropic':
        # Compact groups stretched by a linear transform.
        X, _ = make_blobs(n_samples=n_samples, centers=3, cluster_std=0.7, random_state=42)
        transform = np.array([[1.8, -0.65], [0.35, 0.75]])
        X = X @ transform
    elif preset_type == 'outliers':
        # Compact groups with background noise and several far outliers.
        core_count, noise_count, outlier_count = _split_counts(n_samples, [0.78, 0.17, 0.05])
        X_core, _ = make_blobs(n_samples=core_count, centers=3, cluster_std=0.45, random_state=7)
        rng = np.random.default_rng(42)
        X_noise = rng.uniform(low=-4.5, high=7.5, size=(noise_count, 2))
        X_outliers = np.array([
            [-7.0, -5.5],
            [8.0, -5.0],
            [-6.0, 8.0],
            [9.0, 7.5],
        ])
        if outlier_count > len(X_outliers):
            extra = rng.uniform(low=-8.5, high=9.5, size=(outlier_count - len(X_outliers), 2))
            X_outliers = np.vstack([X_outliers, extra])
        X = np.vstack([X_core, X_noise, X_outliers[:outlier_count]])
    elif preset_type == 'many_blobs':
        # Several compact groups for algorithms that choose representatives or compress data.
        centers = [(-4, -3), (-2, 2.5), (0, -1), (2.5, 2.8), (4.5, -2.2), (6, 1.2), (1.5, -4.5)]
        X, _ = make_blobs(n_samples=n_samples, centers=centers, cluster_std=0.35, random_state=9)
    elif preset_type == 'bridge':
        # Two dense groups connected by a weak chain of points.
        left_count, right_count, bridge_count = _split_counts(n_samples, [0.42, 0.42, 0.16])
        X_left, _ = make_blobs(n_samples=left_count, centers=[(-3, 0)], cluster_std=0.45, random_state=11)
        X_right, _ = make_blobs(n_samples=right_count, centers=[(3, 0)], cluster_std=0.45, random_state=12)
        rng = np.random.default_rng(13)
        x = np.linspace(-2.4, 2.4, bridge_count)
        y = rng.normal(0, 0.16, bridge_count)
        X_bridge = np.column_stack([x, y])
        X = np.vstack([X_left, X_right, X_bridge])
    else:
        raise ValueError(f"Unknown preset type: {preset_type}")
    
    # Normalize with Aspect Ratio Preservation
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    
    # Calculate scale factor to fit in 8x8 box (leaving margin)
    ranges = X_max - X_min
    max_range = ranges.max()
    if max_range == 0:
        scale = 1
    else:
        scale = 8.0 / max_range
    
    # Center the data first (around 0) -> Scale -> Move to 5,5
    # Careful: If we just subtract X_min, we shift to corner.
    # Center of mass of bounding box:
    center = (X_max + X_min) / 2
    
    X_centered = (X - center) * scale # Now centered at 0,0 with size <= 8
    X_final = X_centered + 5.0 # Move to center of 10x10 field
    
    return X_final.tolist()
