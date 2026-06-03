SIMULATOR_ALGORITHM_CONCEPT_MAP = {
    'kmeans': 'Algo_KMeans',
    'dbscan': 'Algo_DBSCAN',
    'forel': 'Algo_FOREL',
    'agglomerative': 'Algo_Agglomerative',
    'ward': 'Algo_Ward',
    'meanshift': 'Algo_MeanShift',
    'gmm': 'Algo_GaussianMixtures',
    'spectral': 'Algo_SpectralClustering',
    'optics': 'Algo_OPTICS',
    'affinity': 'Algo_AffinityPropagation',
    'bisecting': 'Algo_BisectingKMeans',
    'birch': 'Algo_BIRCH',
    'minibatch': 'Algo_MiniBatchKMeans',
}

AGGLOMERATIVE_LINKAGES = ('single', 'complete', 'average')
SIMULATOR_DENDROGRAM_ALGORITHMS = {'agglomerative', 'ward', 'bisecting', 'birch'}
ONTOLOGY_ONLY_ALGORITHMS = {'Algo_HDBSCAN', 'Algo_Maximin'}

TASK_CONCEPT_EXPECTATIONS = {
    'kmeans-quiz-basic': 'Algo_KMeans',
    'test-code-kmeans': 'Algo_KMeans',
    'test-code-minibatch': 'Algo_MiniBatchKMeans',
    'test-code-dbscan': 'Algo_DBSCAN',
    'test-code-hdbscan': 'Algo_HDBSCAN',
    'maxmin': 'Algo_Maximin',
}
