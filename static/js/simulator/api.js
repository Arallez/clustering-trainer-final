/**
 * API wrapper for clustering simulator endpoints.
 */

const API_URLS = window.simulatorApiUrls || {
    run: '/simulator/run/',
    preset: '/simulator/preset/',
    dendrogram: '/simulator/dendrogram/',
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getLearningContext() {
    const params = new URLSearchParams(window.location.search);
    return {
        module_slug: params.get('module') || '',
        preset: params.get('preset') || '',
    };
}

async function postData(endpoint, data) {
    const csrftoken = getCookie('csrftoken');
    const payload = {
        ...data,
        ...getLearningContext(),
    };

    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(payload),
    });

    return await response.json();
}

async function getData(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${endpoint}?${query}` : endpoint;
    const response = await fetch(url);
    return await response.json();
}

export const runKMeans = async (points, k) => {
    return await postData(API_URLS.run, {
        algorithm: 'kmeans',
        points,
        params: { k },
    });
};

export const runMiniBatch = async (points, k, batchSize) => {
    return await postData(API_URLS.run, {
        algorithm: 'minibatch',
        points,
        params: { k, batchSize },
    });
};

export const runDBSCAN = async (points, eps, minPts) => {
    return await postData(API_URLS.run, {
        algorithm: 'dbscan',
        points,
        params: { eps, minPts },
    });
};

export const runForel = async (points, radius) => {
    return await postData(API_URLS.run, {
        algorithm: 'forel',
        points,
        params: { radius },
    });
};

export const runAgglomerative = async (points, k, linkage = 'average') => {
    return await postData(API_URLS.run, {
        algorithm: 'agglomerative',
        points,
        params: { k, linkage },
    });
};

export const runWard = async (points, k) => {
    return await postData(API_URLS.run, {
        algorithm: 'ward',
        points,
        params: { k },
    });
};

export const runMeanShift = async (points, bandwidth) => {
    return await postData(API_URLS.run, {
        algorithm: 'meanshift',
        points,
        params: { bandwidth },
    });
};

export const generatePreset = async (name, samples = 100) => {
    return await getData(API_URLS.preset, { name, samples });
};

export const getDendrogram = async (points, algorithm = 'agglomerative', options = {}) => {
    return await postData(API_URLS.dendrogram, {
        points,
        algorithm,
        ...options,
    });
};

export const runGMM = async (points, nComponents) => {
    return await postData(API_URLS.run, {
        algorithm: 'gmm',
        points,
        params: { n_components: nComponents },
    });
};

export const runSpectral = async (points, k, sigma = 1.0) => {
    return await postData(API_URLS.run, {
        algorithm: 'spectral',
        points,
        params: { k, sigma },
    });
};

export const runOPTICS = async (points, minPts, xi = 0.05) => {
    return await postData(API_URLS.run, {
        algorithm: 'optics',
        points,
        params: { minPts, xi },
    });
};

export const runAffinityPropagation = async (points, damping) => {
    return await postData(API_URLS.run, {
        algorithm: 'affinity',
        points,
        params: { damping },
    });
};

export const runBisecting = async (points, k) => {
    return await postData(API_URLS.run, {
        algorithm: 'bisecting',
        points,
        params: { k },
    });
};

export const runBIRCH = async (points, threshold, k) => {
    return await postData(API_URLS.run, {
        algorithm: 'birch',
        points,
        params: { threshold, k },
    });
};
