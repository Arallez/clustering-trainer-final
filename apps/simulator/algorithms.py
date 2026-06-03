import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, cdist
from scipy.linalg import eigh
from sklearn.cluster import MiniBatchKMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics.pairwise import rbf_kernel


def to_python_types(obj):
    """
    Convert numpy types to native Python types for JSON serialization.
    Handles int64, float64, arrays, and nested structures.
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(to_python_types(item) for item in obj)
    return obj


def clean_floats(obj):
    """
    Clean floats for JSON serialization.
    Handles numpy scalars and nested structures.
    """
    if isinstance(obj, list):
        return [clean_floats(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: clean_floats(v) for k, v in obj.items()}
    elif hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    return obj


def normalize_points(points):
    """
    Convert points from list of dicts [{'x': 1, 'y': 2}] or list of lists 
    to numpy array [[1, 2]].
    """
    if not points:
        return np.array([])
    
    # If already numpy array, just return
    if isinstance(points, np.ndarray):
        return points

    # Check first element to see format
    first = points[0]
    if isinstance(first, dict) and 'x' in first and 'y' in first:
        return np.array([[p['x'], p['y']] for p in points])
    elif isinstance(first, (list, tuple)):
        return np.array(points)
    
    return np.array(points)

def kmeans_step(points, k):
    X = normalize_points(points)
    if len(X) < k:
        return []
    
    # Randomly initialize centroids
    indices = np.random.choice(len(X), k, replace=False)
    centroids = X[indices]
    
    history = []
    max_iters = 100
    
    for _ in range(max_iters):
        # Calculate distances
        distances = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)
        labels = np.argmin(distances, axis=1)
        
        step_data = {
            'centroids': [{'x': c[0], 'y': c[1]} for c in centroids],
            'labels': labels.tolist()
        }
        history.append(step_data)
        
        new_centroids = np.array([X[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i] for i in range(k)])
        
        if np.allclose(centroids, new_centroids):
            break
            
        centroids = new_centroids
        
    return history

def dbscan_step(points, eps, min_pts):
    X = normalize_points(points)
    n = len(X)
    labels = -1 * np.ones(n, dtype=int)  # -1 = noise
    visited = np.zeros(n, dtype=bool)
    cluster_id = 0
    history = []

    def get_neighbors(idx):
        return np.where(np.linalg.norm(X - X[idx], axis=1) <= eps)[0]

    for i in range(n):
        if visited[i]:
            continue
            
        visited[i] = True
        neighbors = get_neighbors(i)
        
        # Snapshot for visualization (visiting point i)
        history.append({
            'labels': labels.tolist(),
            'current': int(i),
            'neighbors': neighbors.tolist()
        })

        if len(neighbors) < min_pts:
            labels[i] = -1 # Noise
        else:
            labels[i] = cluster_id
            seeds = list(neighbors)
            if i in seeds:
                seeds.remove(i)
            
            while seeds:
                curr_p = seeds.pop(0)
                if not visited[curr_p]:
                    visited[curr_p] = True
                    curr_neighbors = get_neighbors(curr_p)
                    if len(curr_neighbors) >= min_pts:
                        seeds.extend(curr_neighbors)
                
                if labels[curr_p] == -1:
                    labels[curr_p] = cluster_id
            
            cluster_id += 1
            
            # Snapshot after forming a cluster
            history.append({
                'labels': labels.tolist(),
                'current': None,
                'neighbors': []
            })
            
    # Final state
    history.append({
        'labels': labels.tolist(),
        'current': None,
        'neighbors': []
    })
    
    return history

def forel_step(points, r):
    X = normalize_points(points)
    n = len(X)
    labels = -1 * np.ones(n, dtype=int)
    remaining_indices = np.arange(n)
    cluster_id = 0
    history = []
    
    while len(remaining_indices) > 0:
        # Pick random point as start center
        current_idx = np.random.choice(remaining_indices)
        center = X[current_idx]
        
        while True:
            # Find neighbors in radius R
            dists = np.linalg.norm(X[remaining_indices] - center, axis=1)
            neighbors_mask = dists <= r
            neighbors_indices = remaining_indices[neighbors_mask]
            
            step_data = {
                'labels': labels.tolist(),
                'center': {'x': center[0], 'y': center[1]},
                'radius': r,
                'active_indices': neighbors_indices.tolist()
            }
            history.append(step_data)
            
            if len(neighbors_indices) == 0:
                break
                
            new_center = np.mean(X[neighbors_indices], axis=0)
            
            if np.linalg.norm(new_center - center) < 1e-4:
                # Stabilized
                labels[neighbors_indices] = cluster_id
                
                # Remove clustered points
                remaining_mask = np.ones(len(remaining_indices), dtype=bool)
                remaining_mask[neighbors_mask] = False
                remaining_indices = remaining_indices[remaining_mask]
                
                cluster_id += 1
                break
            
            center = new_center
            
    # Final state
    history.append({
        'labels': labels.tolist(),
        'center': None,
        'radius': r,
        'active_indices': []
    })
            
    return history

def _hierarchical_step(points, n_clusters, linkage_method):
    """
    Shared helper for hierarchical clustering variants.
    """
    X = normalize_points(points)
    n = len(X)
    
    if n < 2:
        return [{'labels': [0] * n}]

    Z = linkage(X, method=linkage_method)
    
    history = []
    
    start_k = min(n, 50)
    target_k = max(1, n_clusters)
    
    for k in range(start_k, target_k - 1, -1):
        labels = fcluster(Z, k, criterion='maxclust')
        labels = labels - 1
        history.append({'labels': labels.tolist()})
        
    if not history:
        labels = fcluster(Z, target_k, criterion='maxclust') - 1
        history.append({'labels': labels.tolist()})

    return history


def agglomerative_step(points, n_clusters, linkage_method='average'):
    """
    Generic agglomerative clustering with selectable linkage.
    """
    return _hierarchical_step(points, n_clusters, linkage_method)


def ward_step(points, n_clusters):
    """
    Dedicated Ward hierarchical clustering.
    """
    return _hierarchical_step(points, n_clusters, 'ward')

def mean_shift_step(points, bandwidth=1.0):
    """
    Optimized MeanShift using Vectorization.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples == 0:
        return []
        
    centroids = np.copy(X)
    history = []
    
    max_iters = 100
    stop_thresh = 1e-3 * bandwidth
    
    for it in range(max_iters):
        old_centroids = np.copy(centroids)
        
        # Vectorized distance calculation (N x N)
        dists = cdist(centroids, centroids)
        
        # Weights matrix (N x N)
        weights = (dists <= bandwidth).astype(float)
        
        # Sum of weights for each point (denominator)
        denoms = weights.sum(axis=1, keepdims=True)
        
        # Avoid division by zero
        denoms[denoms == 0] = 1.0
        
        # New centroids
        new_centroids = np.dot(weights, centroids) / denoms
        
        # Visualization: Group nearby centroids
        rounded = np.round(new_centroids, decimals=1)
        unique_pos, inverse_indices = np.unique(rounded, axis=0, return_inverse=True)
        
        step_data = {
            'centroids': [{'x': float(c[0]), 'y': float(c[1])} for c in unique_pos],
            'labels': inverse_indices.tolist()
        }
        history.append(step_data)
        
        # Check convergence
        shift = np.linalg.norm(new_centroids - old_centroids, axis=1)
        if np.max(shift) < stop_thresh:
            break
            
        centroids = new_centroids

    return history

def compute_dendrogram_data(points, linkage_method='ward'):
    """
    Compute dendrogram data and return JSON-serializable structure.
    """
    X = normalize_points(points)
    if len(X) < 2:
        return {'error': "Need at least 2 points"}
        
    Z = linkage(X, method=linkage_method)
    ddata = dendrogram(Z, no_plot=True)
    
    return clean_floats(ddata)


# ==================== NEW ALGORITHMS ====================

def gmm_step(points, n_components, max_iters=100):
    """
    Gaussian Mixture Models with EM algorithm.
    Returns history of iterations showing means, covariances, and responsibilities.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < n_components:
        return []
    
    history = []
    
    # Initialize means randomly from data points
    np.random.seed(42)  # For reproducibility
    indices = np.random.choice(n_samples, n_components, replace=False)
    means = X[indices].copy()
    
    # Initialize covariances as identity matrices
    covariances = np.array([np.eye(2) for _ in range(n_components)])
    
    # Initialize mixing weights uniformly
    weights = np.ones(n_components) / n_components
    
    for iteration in range(max_iters):
        # E-step: Calculate responsibilities
        responsibilities = np.zeros((n_samples, n_components))
        
        for k in range(n_components):
            # Calculate multivariate Gaussian probability
            diff = X - means[k]
            try:
                # Add small regularization for numerical stability
                cov_reg = covariances[k] + 1e-6 * np.eye(2)
                det = np.linalg.det(cov_reg)
                if det <= 0:
                    det = 1e-6
                inv_cov = np.linalg.inv(cov_reg)
                exponent = -0.5 * np.sum(diff @ inv_cov * diff, axis=1)
                responsibilities[:, k] = weights[k] * np.exp(exponent) / np.sqrt(det * (2 * np.pi) ** 2)
            except np.linalg.LinAlgError:
                responsibilities[:, k] = weights[k] / n_components
        
        # Normalize responsibilities
        resp_sum = responsibilities.sum(axis=1, keepdims=True)
        resp_sum[resp_sum == 0] = 1e-10
        responsibilities /= resp_sum
        
        # Get hard labels for visualization
        labels = np.argmax(responsibilities, axis=1)
        
        # Store step data
        step_data = {
            'centroids': [{'x': float(m[0]), 'y': float(m[1])} for m in means],
            'labels': labels.tolist(),
            'probabilities': responsibilities.max(axis=1).tolist()  # Confidence
        }
        history.append(step_data)
        
        # M-step: Update parameters
        Nk = responsibilities.sum(axis=0)
        Nk[Nk == 0] = 1e-10  # Avoid division by zero
        
        new_means = np.zeros_like(means)
        new_covariances = np.zeros_like(covariances)
        
        for k in range(n_components):
            # Update means
            new_means[k] = np.sum(responsibilities[:, k:k+1] * X, axis=0) / Nk[k]
            
            # Update covariances
            diff = X - new_means[k]
            new_covariances[k] = (responsibilities[:, k:k+1] * diff).T @ diff / Nk[k]
        
        # Update weights
        new_weights = Nk / n_samples
        
        # Check convergence
        if np.allclose(means, new_means, atol=1e-4):
            break
            
        means = new_means
        covariances = new_covariances
        weights = new_weights
    
    return to_python_types(history)


def spectral_step(points, n_clusters, sigma=1.0):
    """
    Spectral Clustering using normalized Laplacian.
    Shows the embedding space transformation and final clustering.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < n_clusters:
        return []
    
    history = []
    
    # Step 1: Compute similarity matrix (RBF kernel)
    similarity = rbf_kernel(X, gamma=1.0 / (2 * sigma ** 2))
    
    # Store initial state
    history.append({
        'phase': 'similarity',
        'description': 'Вычисление матрицы сходства',
        'labels': [0] * n_samples
    })
    
    # Step 2: Compute degree matrix and Laplacian
    degree = np.diag(similarity.sum(axis=1))
    laplacian_matrix = degree - similarity
    
    # Normalized Laplacian: L_sym = D^(-1/2) L D^(-1/2)
    degree_inv_sqrt = np.diag(1.0 / np.sqrt(similarity.sum(axis=1) + 1e-10))
    laplacian_normalized = degree_inv_sqrt @ laplacian_matrix @ degree_inv_sqrt
    
    history.append({
        'phase': 'laplacian',
        'description': 'Вычисление Лапласиана',
        'labels': [0] * n_samples
    })
    
    # Step 3: Compute eigenvectors
    eigenvalues, eigenvectors = eigh(laplacian_normalized)
    
    # Take first k eigenvectors
    embedding = eigenvectors[:, :n_clusters]
    
    # Normalize rows
    row_norms = np.linalg.norm(embedding, axis=1, keepdims=True)
    row_norms[row_norms == 0] = 1
    embedding = embedding / row_norms
    
    history.append({
        'phase': 'embedding',
        'description': f'Спектральное вложение (k={n_clusters})',
        'labels': [0] * n_samples
    })
    
    # Step 4: K-means on embedding
    # Initialize centroids
    indices = np.random.choice(n_samples, n_clusters, replace=False)
    centroids = embedding[indices]
    
    for iteration in range(50):
        distances = np.linalg.norm(embedding[:, np.newaxis] - centroids, axis=2)
        labels = np.argmin(distances, axis=1)
        
        # Map back to original space for visualization
        step_data = {
            'phase': 'clustering',
            'description': f'K-Means на вложении (итерация {iteration + 1})',
            'labels': labels.tolist()
        }
        history.append(step_data)
        
        new_centroids = np.array([
            embedding[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i]
            for i in range(n_clusters)
        ])
        
        if np.allclose(centroids, new_centroids):
            break
            
        centroids = new_centroids
    
    return to_python_types(history)


def optics_step(points, min_pts, xi=0.05):
    """
    OPTICS (Ordering Points To Identify the Clustering Structure).
    Creates an ordering of points based on reachability distance.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < min_pts:
        return []
    
    history = []
    
    # Use a large finite value instead of inf for JSON serialization
    LARGE_VAL = 1e10
    
    # Compute core distances
    def compute_core_distance(idx):
        distances = np.linalg.norm(X - X[idx], axis=1)
        distances.sort()
        return distances[min_pts - 1] if len(distances) >= min_pts else LARGE_VAL
    
    core_distances = np.array([compute_core_distance(i) for i in range(n_samples)])
    
    # OPTICS ordering
    processed = np.zeros(n_samples, dtype=bool)
    reachability = np.full(n_samples, LARGE_VAL)
    ordering = []
    
    labels = -1 * np.ones(n_samples, dtype=int)
    
    for start_idx in range(n_samples):
        if processed[start_idx]:
            continue
        
        # Start new cluster expansion
        seeds = [(start_idx, LARGE_VAL)]
        
        while seeds:
            # Get point with smallest reachability
            seeds.sort(key=lambda x: x[1])
            current_idx, _ = seeds.pop(0)
            
            if processed[current_idx]:
                continue
                
            processed[current_idx] = True
            ordering.append(current_idx)
            
            # Find neighbors - use reasonable radius
            distances = np.linalg.norm(X - X[current_idx], axis=1)
            radius = min(core_distances[current_idx] * 2, 10.0)  # Cap radius
            neighbors = np.where(distances <= radius)[0]
            
            # Update reachability for neighbors
            for neighbor in neighbors:
                if processed[neighbor]:
                    continue
                    
                new_reachability = max(core_distances[current_idx], 
                                       np.linalg.norm(X[current_idx] - X[neighbor]))
                
                if new_reachability < reachability[neighbor]:
                    reachability[neighbor] = new_reachability
                    seeds.append((neighbor, new_reachability))
            
            # Record step - replace inf with null for JSON
            reachability_json = [None if r >= LARGE_VAL else float(r) for r in reachability]
            history.append({
                'labels': labels.tolist(),
                'current': int(current_idx),
                'ordering': list(ordering),
                'reachability': reachability_json
            })
    
    # Extract clusters using xi method (simplified)
    # Find valleys in reachability plot
    finite_reachability = reachability[reachability < LARGE_VAL]
    if len(finite_reachability) > 0:
        threshold = np.median(finite_reachability) * (1 + xi)
    else:
        threshold = LARGE_VAL
    
    in_cluster = False
    cluster_id = 0
    for i, idx in enumerate(ordering):
        if reachability[idx] < threshold:
            if not in_cluster:
                in_cluster = True
                cluster_id += 1
            labels[idx] = cluster_id - 1
        else:
            in_cluster = False
            labels[idx] = -1  # Noise
    
    # Final state
    reachability_json = [None if r >= LARGE_VAL else float(r) for r in reachability]
    history.append({
        'labels': labels.tolist(),
        'current': None,
        'ordering': list(ordering),
        'reachability': reachability_json
    })
    
    return to_python_types(history)


def bisecting_kmeans_step(points, n_clusters, max_iters=100):
    """
    Bisecting K-Means (Divisive Hierarchical Clustering).
    Builds a binary tree by repeatedly splitting clusters using K-Means.
    Returns history with dendrogram data included in final step.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < 2:
        return []
    
    history = []
    
    # Track splits for dendrogram construction
    # Each split: {parent_node, left_node, right_node, left_indices, right_indices, distance}
    splits = []
    
    # Node counter: leaf nodes (points) are 0..n_samples-1, internal nodes start at n_samples
    next_node_id = n_samples
    
    # Current clusters to split: list of (indices, node_id)
    current_clusters = [(list(range(n_samples)), next_node_id)]
    next_node_id += 1
    
    while len(current_clusters) < n_clusters and current_clusters:
        # Find cluster with largest SSE to split
        best_sse = -1
        best_cluster_idx = 0
        
        for idx, (indices, node_id) in enumerate(current_clusters):
            if len(indices) < 2:
                continue
            cluster_points = X[indices]
            centroid = cluster_points.mean(axis=0)
            sse = np.sum((cluster_points - centroid) ** 2)
            if sse > best_sse:
                best_sse = sse
                best_cluster_idx = idx
        
        # Get cluster to split
        indices_to_split, parent_node_id = current_clusters.pop(best_cluster_idx)
        
        if len(indices_to_split) < 2:
            current_clusters.append((indices_to_split, parent_node_id))
            break
        
        # Run K-Means with k=2
        cluster_points = X[indices_to_split]
        
        # Initialize centroids (k-means++ style)
        centroid = cluster_points.mean(axis=0)
        dists = np.linalg.norm(cluster_points - centroid, axis=1)
        seed1_idx = np.argmax(dists)
        seed1 = cluster_points[seed1_idx]
        dists_from_seed1 = np.linalg.norm(cluster_points - seed1, axis=1)
        seed2_idx = np.argmax(dists_from_seed1)
        seed2 = cluster_points[seed2_idx]
        
        centroids = np.array([seed1, seed2])
        
        # Run K-Means iterations
        for _ in range(max_iters):
            distances = np.linalg.norm(cluster_points[:, np.newaxis] - centroids, axis=2)
            labels = np.argmin(distances, axis=1)
            
            new_centroids = np.array([
                cluster_points[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i]
                for i in range(2)
            ])
            
            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids
        
        # Split into left and right children
        left_indices = [indices_to_split[i] for i in range(len(indices_to_split)) if labels[i] == 0]
        right_indices = [indices_to_split[i] for i in range(len(indices_to_split)) if labels[i] == 1]
        
        if len(left_indices) == 0 or len(right_indices) == 0:
            current_clusters.append((indices_to_split, parent_node_id))
            continue
        
        # Distance between centroids (for dendrogram height)
        split_distance = np.linalg.norm(centroids[0] - centroids[1])
        
        # Create child node IDs
        left_node_id = next_node_id
        next_node_id += 1
        right_node_id = next_node_id
        next_node_id += 1
        
        # Record this split for dendrogram
        splits.append({
            'parent_node': parent_node_id,
            'left_node': left_node_id,
            'right_node': right_node_id,
            'left_indices': left_indices,
            'right_indices': right_indices,
            'distance': split_distance
        })
        
        # Add child clusters
        current_clusters.append((left_indices, left_node_id))
        current_clusters.append((right_indices, right_node_id))
        
        # Update labels for visualization
        temp_labels = np.zeros(n_samples, dtype=int) - 1
        for cluster_idx, (indices, _) in enumerate(current_clusters):
            for idx in indices:
                temp_labels[idx] = cluster_idx
        
        history.append({
            'labels': temp_labels.tolist(),
            'n_clusters': len(current_clusters),
            'split_info': {
                'parent_size': len(indices_to_split),
                'left_size': len(left_indices),
                'right_size': len(right_indices)
            }
        })
    
    # Final labels
    final_labels = np.zeros(n_samples, dtype=int)
    for cluster_idx, (indices, _) in enumerate(current_clusters):
        for idx in indices:
            final_labels[idx] = cluster_idx
    
    # Build dendrogram from splits
    dendrogram_data = _build_divisive_dendrogram(splits, n_samples)
    
    history.append({
        'labels': final_labels.tolist(),
        'n_clusters': len(current_clusters),
        'final': True,
        'dendrogram': dendrogram_data
    })
    
    return to_python_types(history)


def _build_divisive_dendrogram(splits, n_samples):
    """
    Build dendrogram coordinates (icoord, dcoord) from split history.
    This creates a proper divisive dendrogram visualization.
    
    For divisive clustering, the dendrogram shows splits from top (root) to bottom (leaves).
    The height represents when a cluster was split.
    """
    if not splits:
        return {'icoord': [], 'dcoord': []}
    
    # Build children map from splits
    children_map = {}
    # Also build parent map to find all nodes
    parent_map = {}
    for split in splits:
        children_map[split['parent_node']] = {
            'left': split['left_node'],
            'right': split['right_node'],
            'distance': split['distance'],
            'left_indices': split['left_indices'],
            'right_indices': split['right_indices']
        }
        parent_map[split['left_node']] = split['parent_node']
        parent_map[split['right_node']] = split['parent_node']
    
    # Find root node (node with no parent)
    all_nodes = set()
    for split in splits:
        all_nodes.add(split['parent_node'])
        all_nodes.add(split['left_node'])
        all_nodes.add(split['right_node'])
    
    root_node = None
    for node in all_nodes:
        if node not in parent_map:
            root_node = node
            break
    
    if root_node is None:
        root_node = splits[0]['parent_node']
    
    # Collect leaf order by traversing tree left-to-right
    leaf_order = []
    
    def collect_leaves(node_id):
        if node_id < n_samples:
            # It's a leaf (original point)
            leaf_order.append(node_id)
            return
        if node_id in children_map:
            collect_leaves(children_map[node_id]['left'])
            collect_leaves(children_map[node_id]['right'])
    
    collect_leaves(root_node)
    
    # If leaf_order is empty or incomplete, add all leaves directly
    all_leaves = set(range(n_samples))
    for leaf in all_leaves:
        if leaf not in leaf_order:
            leaf_order.append(leaf)
    
    # Map leaf to x position (with spacing) - scipy style
    x_spacing = 10  # Spacing between leaves
    leaf_x = {leaf: i * x_spacing + 5 for i, leaf in enumerate(leaf_order)}
    
    # Compute node heights (distance from root)
    # For divisive dendrogram, height = cumulative distance from root
    node_heights = {}
    
    def compute_heights(node_id, current_height=0):
        """Compute height for each node based on cumulative split distance."""
        node_heights[node_id] = current_height
        if node_id in children_map:
            children = children_map[node_id]
            # Children are at height = parent_height + split_distance
            new_height = current_height + children['distance']
            compute_heights(children['left'], new_height)
            compute_heights(children['right'], new_height)
    
    compute_heights(root_node, 0)
    
    # Find max height for scaling
    max_height = max(node_heights.values()) if node_heights else 1
    if max_height == 0:
        max_height = 1
    
    # Build dendrogram coordinates
    icoord = []
    dcoord = []
    
    # Node x positions cache
    node_x = {}
    
    def get_node_x(node_id):
        """Get x position for a node (cached)."""
        if node_id in node_x:
            return node_x[node_id]
        
        if node_id < n_samples:
            # Leaf node - use position from leaf_x
            x = leaf_x.get(node_id, 0)
            node_x[node_id] = x
            return x
        
        if node_id in children_map:
            # Internal node that was split - compute from children
            children = children_map[node_id]
            left_x = get_node_x(children['left'])
            right_x = get_node_x(children['right'])
            x = (left_x + right_x) / 2
            node_x[node_id] = x
            return x
        
        # Unexpanded internal node (leaf in final clustering)
        # Find its point indices and compute center
        for split in splits:
            if node_id == split['left_node']:
                xs = [leaf_x.get(i, 5) for i in split['left_indices']]
                if xs:
                    x = sum(xs) / len(xs)
                    node_x[node_id] = x
                    return x
            elif node_id == split['right_node']:
                xs = [leaf_x.get(i, 5) for i in split['right_indices']]
                if xs:
                    x = sum(xs) / len(xs)
                    node_x[node_id] = x
                    return x
        
        # Fallback
        node_x[node_id] = 5
        return 5
    
    # Build coordinates for each split
    for split in splits:
        parent_node = split['parent_node']
        if parent_node not in children_map:
            continue
            
        children = children_map[parent_node]
        left_node = children['left']
        right_node = children['right']
        
        left_x = get_node_x(left_node)
        right_x = get_node_x(right_node)
        
        parent_height = node_heights.get(parent_node, 0)
        split_height = parent_height + children['distance']
        
        # Draw the "inverted U" shape for this split
        # For divisive: start at parent height, go down to split height, back to parent height
        # The shape: left_x at parent_height -> left_x at split_height -> right_x at split_height -> right_x at parent_height
        icoord.append([left_x, left_x, right_x, right_x])
        dcoord.append([parent_height, split_height, split_height, parent_height])
    
    if not icoord:
        return {'icoord': [], 'dcoord': []}
    
    # Scale heights for better visualization (max height = 5)
    scale_factor = 5.0 / max_height if max_height > 0 else 1.0
    dcoord = [[d * scale_factor for d in coords] for coords in dcoord]
    
    return {'icoord': icoord, 'dcoord': dcoord}


def compute_bisecting_dendrogram(points, n_clusters=None):
    """
    Compute dendrogram data for Bisecting K-Means.
    Returns data in scipy dendrogram format.
    
    Bisecting K-Means is a DIVISIVE hierarchical method:
    - Starts with all points in one cluster
    - Recursively splits clusters using K-Means (k=2)
    - Builds tree TOP-DOWN (divisive)
    
    The dendrogram shows the order and structure of splits.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < 2:
        return {'error': 'Need at least 2 points'}
    
    # Run bisecting k-means to get splits
    splits = []
    next_node_id = n_samples
    
    # Current clusters to split: list of (indices, node_id)
    current_clusters = [(list(range(n_samples)), next_node_id)]
    next_node_id += 1
    
    # Continue splitting until we can't split anymore (for full dendrogram)
    while current_clusters:
        # Find cluster with largest SSE to split
        best_sse = -1
        best_cluster_idx = 0
        
        for idx, (indices, node_id) in enumerate(current_clusters):
            if len(indices) < 2:
                continue
            cluster_points = X[indices]
            centroid = cluster_points.mean(axis=0)
            sse = np.sum((cluster_points - centroid) ** 2)
            if sse > best_sse:
                best_sse = sse
                best_cluster_idx = idx
        
        # Get cluster to split
        indices_to_split, parent_node_id = current_clusters.pop(best_cluster_idx)
        
        if len(indices_to_split) < 2:
            current_clusters.append((indices_to_split, parent_node_id))
            break
        
        # Run K-Means with k=2
        cluster_points = X[indices_to_split]
        
        # Initialize centroids (k-means++ style)
        centroid = cluster_points.mean(axis=0)
        dists = np.linalg.norm(cluster_points - centroid, axis=1)
        seed1_idx = np.argmax(dists)
        seed1 = cluster_points[seed1_idx]
        dists_from_seed1 = np.linalg.norm(cluster_points - seed1, axis=1)
        seed2_idx = np.argmax(dists_from_seed1)
        seed2 = cluster_points[seed2_idx]
        
        centroids = np.array([seed1, seed2])
        
        # Run K-Means iterations
        for _ in range(100):
            distances = np.linalg.norm(cluster_points[:, np.newaxis] - centroids, axis=2)
            labels = np.argmin(distances, axis=1)
            
            new_centroids = np.array([
                cluster_points[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i]
                for i in range(2)
            ])
            
            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids
        
        # Split into left and right children
        left_indices = [indices_to_split[i] for i in range(len(indices_to_split)) if labels[i] == 0]
        right_indices = [indices_to_split[i] for i in range(len(indices_to_split)) if labels[i] == 1]
        
        if len(left_indices) == 0 or len(right_indices) == 0:
            current_clusters.append((indices_to_split, parent_node_id))
            continue
        
        # Distance between centroids (for dendrogram height)
        split_distance = np.linalg.norm(centroids[0] - centroids[1])
        
        # Create child node IDs
        left_node_id = next_node_id
        next_node_id += 1
        right_node_id = next_node_id
        next_node_id += 1
        
        # Record this split for dendrogram
        splits.append({
            'parent_node': parent_node_id,
            'left_node': left_node_id,
            'right_node': right_node_id,
            'left_indices': left_indices,
            'right_indices': right_indices,
            'distance': split_distance
        })
        
        # Add child clusters for further splitting
        current_clusters.append((left_indices, left_node_id))
        current_clusters.append((right_indices, right_node_id))
    
    # Build dendrogram using the same function as bisecting_kmeans_step
    return _build_divisive_dendrogram(splits, n_samples)


def birch_step(points, threshold=0.5, branching_factor=50, n_clusters=None):
    """
    BIRCH (Balanced Iterative Reducing and Clustering using Hierarchies).
    Builds a CF-tree and then clusters the subclusters.
    Returns history with CF-tree structure.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < 2:
        return []
    
    history = []
    
    # CF (Clustering Feature) representation: (N, LS, SS)
    # N = number of points, LS = linear sum, SS = square sum
    class CFNode:
        def __init__(self):
            self.n = 0
            self.ls = np.zeros(2)
            self.ss = np.zeros(2)
            self.children = []  # For non-leaf nodes
            self.cf_entries = []  # For leaf nodes
            self.is_leaf = True
        
        def add_point(self, point):
            self.n += 1
            self.ls += point
            self.ss += point ** 2
        
        def add_cf_entry(self, entry):
            """Merge a CF entry into this node"""
            self.n += entry['n']
            self.ls += entry['ls']
            self.ss += entry['ss']
        
        def centroid(self):
            if self.n == 0:
                return np.zeros(2)
            return self.ls / self.n
        
        def radius(self):
            if self.n == 0:
                return 0
            return np.sqrt((self.ss / self.n) - (self.ls / self.n) ** 2).mean()
    
    # Simplified BIRCH: collect micro-clusters
    cf_entries = []  # List of {n, ls, ss, points}
    
    for i, point in enumerate(X):
        # Find closest CF entry
        if not cf_entries:
            cf_entries.append({
                'n': 1,
                'ls': point.copy(),
                'ss': point ** 2,
                'points': [i]
            })
        else:
            # Find nearest CF
            min_dist = float('inf')
            nearest_idx = -1
            
            for j, cf in enumerate(cf_entries):
                centroid = cf['ls'] / cf['n']
                dist = np.linalg.norm(point - centroid)
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = j
            
            # Check if can absorb
            if min_dist <= threshold:
                # Absorb into existing CF
                cf_entries[nearest_idx]['n'] += 1
                cf_entries[nearest_idx]['ls'] += point
                cf_entries[nearest_idx]['ss'] += point ** 2
                cf_entries[nearest_idx]['points'].append(i)
            else:
                # Create new CF
                cf_entries.append({
                    'n': 1,
                    'ls': point.copy(),
                    'ss': point ** 2,
                    'points': [i]
                })
        
        # Record step periodically
        if i % 10 == 0 or i == n_samples - 1:
            # Assign labels based on current CF entries
            temp_labels = np.zeros(n_samples, dtype=int) - 1
            for cf_idx, cf in enumerate(cf_entries):
                for p_idx in cf['points']:
                    temp_labels[p_idx] = cf_idx
            
            history.append({
                'phase': 'building',
                'description': f'Построение CF-дерева (точка {i + 1}/{n_samples})',
                'labels': temp_labels.tolist(),
                'n_micro_clusters': len(cf_entries),
                'micro_centroids': [cf['ls'] / cf['n'] for cf in cf_entries]
            })
    
    # Now cluster the micro-clusters using agglomerative clustering
    if len(cf_entries) > 1:
        # Get centroids of micro-clusters
        micro_centroids = np.array([cf['ls'] / cf['n'] for cf in cf_entries])
        micro_weights = np.array([cf['n'] for cf in cf_entries])
        
        # Apply agglomerative clustering on micro-clusters
        if n_clusters is None:
            n_clusters = max(2, len(cf_entries) // 3)
        
        Z = linkage(micro_centroids, method='ward')
        micro_labels = fcluster(Z, n_clusters, criterion='maxclust') - 1
        
        # Build dendrogram data from micro-clusters
        ddata = dendrogram(Z, no_plot=True)
        dendrogram_data = clean_floats(ddata)
        
        # Map back to original points
        final_labels = np.zeros(n_samples, dtype=int)
        for cf_idx, cf in enumerate(cf_entries):
            for p_idx in cf['points']:
                final_labels[p_idx] = micro_labels[cf_idx]
        
        history.append({
            'phase': 'clustering',
            'description': f'Кластеризация микро-кластеров (k={n_clusters})',
            'labels': final_labels.tolist(),
            'n_clusters': n_clusters,
            'final': True,
            'dendrogram': dendrogram_data
        })
    else:
        # Only one micro-cluster
        history.append({
            'phase': 'done',
            'description': 'Все точки в одном кластере',
            'labels': [0] * n_samples,
            'n_clusters': 1,
            'final': True,
            'dendrogram': {'icoord': [], 'dcoord': []}
        })
    
    return to_python_types(history)


def compute_birch_dendrogram(points, threshold=0.5):
    """
    Compute dendrogram for BIRCH by clustering the micro-clusters.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < 2:
        return {'error': 'Need at least 2 points'}
    
    # Build CF entries
    cf_entries = []
    
    for point in X:
        if not cf_entries:
            cf_entries.append({
                'n': 1,
                'ls': point.copy(),
                'ss': point ** 2
            })
        else:
            min_dist = float('inf')
            nearest_idx = -1
            
            for j, cf in enumerate(cf_entries):
                centroid = cf['ls'] / cf['n']
                dist = np.linalg.norm(point - centroid)
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = j
            
            if min_dist <= threshold:
                cf_entries[nearest_idx]['n'] += 1
                cf_entries[nearest_idx]['ls'] += point
                cf_entries[nearest_idx]['ss'] += point ** 2
            else:
                cf_entries.append({
                    'n': 1,
                    'ls': point.copy(),
                    'ss': point ** 2
                })
    
    # Get micro-cluster centroids
    micro_centroids = np.array([cf['ls'] / cf['n'] for cf in cf_entries])
    
    if len(micro_centroids) < 2:
        return {'error': 'Only one micro-cluster formed'}
    
    # Build dendrogram for micro-clusters
    Z = linkage(micro_centroids, method='ward')
    ddata = dendrogram(Z, no_plot=True)
    
    return clean_floats(ddata)


def minibatch_kmeans_step(points, k, batch_size=None, max_iters=25):
    """
    MiniBatch K-Means with partial_fit updates for visualization.
    """
    X = normalize_points(points)
    n_samples = len(X)

    if n_samples < k:
        return []

    if batch_size is None:
        batch_size = min(max(k * 2, 16), n_samples)
    batch_size = max(k, min(int(batch_size), n_samples))

    model = MiniBatchKMeans(
        n_clusters=k,
        batch_size=batch_size,
        n_init=1,
        random_state=42,
        init='k-means++',
        reassignment_ratio=0.01,
    )
    rng = np.random.default_rng(42)

    history = []
    previous_centroids = None
    stable_steps = 0

    for _ in range(max_iters):
        batch_indices = rng.choice(n_samples, size=batch_size, replace=False)
        model.partial_fit(X[batch_indices])

        centroids = np.asarray(model.cluster_centers_)
        distances = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)
        labels = np.argmin(distances, axis=1)

        history.append({
            'centroids': [{'x': float(c[0]), 'y': float(c[1])} for c in centroids],
            'labels': labels.tolist(),
            'batch_indices': batch_indices.tolist(),
        })

        if previous_centroids is not None and np.allclose(previous_centroids, centroids, atol=1e-3):
            stable_steps += 1
            if stable_steps >= 2:
                break
        else:
            stable_steps = 0

        previous_centroids = centroids.copy()

    return to_python_types(history)


def affinity_propagation_step(points, damping=0.5, max_iters=100):
    """
    Affinity Propagation clustering.
    Finds exemplars (representative points) through message passing.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples < 2:
        return []
    
    history = []
    
    # Compute similarity matrix (negative squared Euclidean distance)
    similarity = -cdist(X, X, 'sqeuclidean')
    
    # Set diagonal to median similarity (preference)
    preference = np.median(similarity)
    np.fill_diagonal(similarity, preference)
    
    # Initialize messages
    responsibility = np.zeros((n_samples, n_samples))
    availability = np.zeros((n_samples, n_samples))
    
    for iteration in range(max_iters):
        # Compute responsibilities
        old_responsibility = responsibility.copy()
        
        for i in range(n_samples):
            for k in range(n_samples):
                max_avail_sim = availability[i, :] + similarity[i, :]
                max_avail_sim[k] = -np.inf
                responsibility[i, k] = similarity[i, k] - np.max(max_avail_sim)
        
        # Damping
        responsibility = damping * old_responsibility + (1 - damping) * responsibility
        
        # Compute availabilities
        old_availability = availability.copy()
        
        for i in range(n_samples):
            for k in range(n_samples):
                if i == k:
                    availability[i, k] = np.sum(np.maximum(0, responsibility[:, k]))
                else:
                    availability[i, k] = np.sum(np.maximum(0, responsibility[:, k])) - \
                                         max(0, responsibility[i, k])
        
        # Damping
        availability = damping * old_availability + (1 - damping) * availability
        
        # Find exemplars
        scores = responsibility + availability
        labels = np.argmax(scores, axis=1)
        exemplars = np.unique(labels)
        
        # Remap labels to consecutive integers
        label_map = {ex: i for i, ex in enumerate(exemplars)}
        labels = np.array([label_map.get(l, -1) for l in labels])
        
        # Store step
        exemplar_points = [{'x': float(X[ex][0]), 'y': float(X[ex][1])} for ex in exemplars]
        
        history.append({
            'labels': labels.tolist(),
            'exemplars': exemplar_points,
            'iteration': iteration + 1,
            'n_clusters': len(exemplars)
        })
        
        # Check convergence (simplified)
        if iteration > 10 and len(exemplars) == len(np.unique(
            np.argmax(responsibility + availability, axis=1))):
            break
    
    return to_python_types(history)
