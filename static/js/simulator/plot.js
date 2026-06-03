const PLOT_ID = 'plot';
let plotResizeObserver = null;

const COLORS = {
    bg: 'rgba(0,0,0,0)',
    text: '#a8a29e',
    grid: 'rgba(255,255,255,0.06)',
    zeroLine: 'rgba(255,255,255,0.1)',
    legendBg: 'rgba(28,25,23,0.9)',
    point: '#d6d3d1',
    pointBorder: '#0c0a09',
    clusters: ['#ef4444', '#6366f1', '#14b8a6', '#f59e0b', '#8b5cf6', '#ec4899', '#22c55e', '#f97316'],
    noise: '#78716c',
    centroid: '#fafaf9',
    scan: '#fde047',
    processed: '#38bdf8',
    activeBatch: '#f97316',
    activeArea: '#facc15',
};

const getBaseLayout = () => ({
    title: false,
    paper_bgcolor: COLORS.bg,
    plot_bgcolor: COLORS.bg,
    font: { color: COLORS.text, family: "'Space Grotesk', sans-serif" },
    margin: { t: 20, b: 40, l: 40, r: 20 },
    xaxis: {
        range: [0, 10],
        gridcolor: COLORS.grid,
        zerolinecolor: COLORS.zeroLine,
        fixedrange: true,
        tickfont: { color: COLORS.text },
    },
    yaxis: {
        range: [0, 10],
        gridcolor: COLORS.grid,
        zerolinecolor: COLORS.zeroLine,
        fixedrange: true,
        tickfont: { color: COLORS.text },
    },
    showlegend: true,
    legend: {
        x: 0,
        y: 1,
        bgcolor: COLORS.legendBg,
        bordercolor: 'rgba(255,255,255,0.1)',
        borderwidth: 1,
        font: { color: COLORS.text, family: "'Space Grotesk', sans-serif" },
    },
    hovermode: false,
    dragmode: false,
});

export function resizePlot() {
    const plotDiv = document.getElementById(PLOT_ID);
    if (!plotDiv || !plotDiv._fullLayout) {
        return;
    }

    Plotly.Plots.resize(plotDiv);
}

function watchPlotSize(plotDiv) {
    if (plotResizeObserver) {
        plotResizeObserver.disconnect();
    }

    if (typeof ResizeObserver !== 'function') {
        return;
    }

    plotResizeObserver = new ResizeObserver(() => {
        window.requestAnimationFrame(resizePlot);
    });
    plotResizeObserver.observe(plotDiv);
}

function normalizePoint(point) {
    return Array.isArray(point) ? { x: point[0], y: point[1] } : point;
}

function xy(points) {
    return {
        x: points.map((point) => normalizePoint(point).x),
        y: points.map((point) => normalizePoint(point).y),
    };
}

function uniqueIndices(indices, max) {
    if (!Array.isArray(indices)) {
        return [];
    }

    return [...new Set(indices.filter((index) => Number.isInteger(index) && index >= 0 && index < max))];
}

function indexedPoints(points, indices) {
    return uniqueIndices(indices, points.length).map((index) => points[index]);
}

function createMarkerTrace(points, config) {
    if (!points.length) {
        return null;
    }

    const coords = xy(points);
    return {
        x: coords.x,
        y: coords.y,
        mode: config.mode || 'markers',
        type: 'scatter',
        name: config.name,
        marker: config.marker,
        line: config.line,
        hoverinfo: 'none',
        showlegend: config.showlegend !== false,
    };
}

function createBackgroundTrace(points) {
    const trace = createMarkerTrace(points, {
        name: 'All points',
        showlegend: false,
        marker: {
            size: 9,
            color: 'rgba(214, 211, 209, 0.22)',
            line: { color: 'rgba(12, 10, 9, 0.35)', width: 1 },
        },
    });
    return trace ? [trace] : [];
}

function createClusterTraces(points, stepData, algorithm) {
    const labels = Array.isArray(stepData.labels) ? stepData.labels : null;
    if (!labels || !labels.length) {
        return [];
    }

    if (algorithm === 'spectral' && stepData.phase && stepData.phase !== 'clustering') {
        return [];
    }

    const maxLabel = Math.max(...labels);
    const traces = [];

    const noiseIndices = [];
    const clusters = Array.from({ length: Math.max(maxLabel + 1, 0) }, () => []);

    labels.forEach((label, index) => {
        if (label === -1) {
            noiseIndices.push(index);
        } else if (clusters[label]) {
            clusters[label].push(index);
        }
    });

    if (noiseIndices.length) {
        const noiseTrace = createMarkerTrace(indexedPoints(points, noiseIndices), {
            name: 'Noise',
            marker: { size: 8, color: COLORS.noise, symbol: 'x' },
        });
        if (noiseTrace) {
            traces.push(noiseTrace);
        }
    }

    clusters.forEach((clusterIndices, index) => {
        if (!clusterIndices.length) {
            return;
        }

        const clusterPoints = indexedPoints(points, clusterIndices);
        const probabilitySlice = Array.isArray(stepData.probabilities)
            ? clusterIndices.map((pointIndex) => Math.max(0.25, Math.min(1, stepData.probabilities[pointIndex] || 0.25)))
            : undefined;

        const clusterTrace = createMarkerTrace(clusterPoints, {
            name: `Cluster ${index + 1}`,
            marker: {
                size: 11,
                color: COLORS.clusters[index % COLORS.clusters.length],
                opacity: probabilitySlice,
                line: { color: 'rgba(12, 10, 9, 0.55)', width: 1.25 },
            },
        });
        if (clusterTrace) {
            traces.push(clusterTrace);
        }
    });

    return traces;
}

function createCentroidTrace(stepData) {
    if (!Array.isArray(stepData.centroids) || !stepData.centroids.length) {
        return [];
    }

    const points = stepData.centroids.map((point) => normalizePoint(point));
    const trace = createMarkerTrace(points, {
        name: 'Centroids',
        marker: {
            symbol: 'x',
            size: 16,
            color: COLORS.centroid,
            line: { width: 3, color: COLORS.pointBorder },
        },
    });
    return trace ? [trace] : [];
}

function createActiveAreaTraces(points, stepData) {
    const traces = [];

    if (stepData.center) {
        const center = normalizePoint(stepData.center);
        const centerTrace = createMarkerTrace([center], {
            name: 'Center',
            marker: {
                symbol: 'cross',
                size: 18,
                color: COLORS.centroid,
                line: { width: 2, color: COLORS.activeArea },
            },
        });
        if (centerTrace) {
            traces.push(centerTrace);
        }

        if (stepData.radius) {
            const theta = Array.from({ length: 72 }, (_, index) => (index * 2 * Math.PI) / 71);
            traces.push({
                x: theta.map((angle) => center.x + stepData.radius * Math.cos(angle)),
                y: theta.map((angle) => center.y + stepData.radius * Math.sin(angle)),
                mode: 'lines',
                type: 'scatter',
                name: 'Search radius',
                line: { color: 'rgba(250, 204, 21, 0.75)', dash: 'dot', width: 2 },
                hoverinfo: 'none',
            });
        }
    }

    const activeIndices = indexedPoints(points, stepData.active_indices);
    if (activeIndices.length) {
        const activeTrace = createMarkerTrace(activeIndices, {
            name: 'Active points',
            marker: {
                size: 14,
                color: 'rgba(250, 204, 21, 0.18)',
                line: { color: COLORS.activeArea, width: 2.5 },
            },
        });
        if (activeTrace) {
            traces.push(activeTrace);
        }
    }

    return traces;
}

function createNeighborhoodTraces(points, stepData) {
    const traces = [];

    const neighborPoints = indexedPoints(points, stepData.neighbors);
    if (neighborPoints.length) {
        const neighborTrace = createMarkerTrace(neighborPoints, {
            name: 'Neighborhood',
            marker: {
                size: 14,
                color: 'rgba(253, 224, 71, 0.15)',
                line: { color: COLORS.scan, width: 2.5 },
            },
        });
        if (neighborTrace) {
            traces.push(neighborTrace);
        }
    }

    if (stepData.current !== undefined && stepData.current !== null && points[stepData.current]) {
        const currentTrace = createMarkerTrace([points[stepData.current]], {
            name: 'Current point',
            marker: {
                size: 18,
                color: 'rgba(0,0,0,0)',
                line: { color: COLORS.scan, width: 3 },
            },
        });
        if (currentTrace) {
            traces.push(currentTrace);
        }
    }

    return traces;
}

function createBatchTrace(points, stepData) {
    const batchPoints = indexedPoints(points, stepData.batch_indices);
    const trace = createMarkerTrace(batchPoints, {
        name: 'Mini-batch',
        marker: {
            size: 15,
            color: 'rgba(249, 115, 22, 0.14)',
            line: { color: COLORS.activeBatch, width: 2.5 },
        },
    });
    return trace ? [trace] : [];
}

function createOrderingTraces(points, stepData) {
    if (!Array.isArray(stepData.ordering)) {
        return [];
    }

    const traces = [];
    const processedIndices = uniqueIndices(stepData.ordering, points.length);
    const processedSet = new Set(processedIndices);
    const remainingIndices = points
        .map((_, index) => index)
        .filter((index) => !processedSet.has(index));

    const processedTrace = createMarkerTrace(indexedPoints(points, processedIndices), {
        name: 'Processed',
        marker: {
            size: 10,
            color: COLORS.processed,
            opacity: 0.9,
            line: { color: 'rgba(12, 10, 9, 0.35)', width: 1 },
        },
    });
    if (processedTrace) {
        traces.push(processedTrace);
    }

    const remainingTrace = createMarkerTrace(indexedPoints(points, remainingIndices), {
        name: 'Not processed',
        marker: {
            size: 9,
            color: 'rgba(214, 211, 209, 0.12)',
            line: { color: 'rgba(12, 10, 9, 0.2)', width: 1 },
        },
    });
    if (remainingTrace) {
        traces.push(remainingTrace);
    }

    return traces;
}

export function initPlot() {
    const plotDiv = document.getElementById(PLOT_ID);
    if (!plotDiv) {
        return;
    }

    Plotly.newPlot(PLOT_ID, [{
        x: [],
        y: [],
        mode: 'markers',
        type: 'scatter',
        hoverinfo: 'none',
    }], getBaseLayout(), {
        displayModeBar: false,
        responsive: true,
        staticPlot: false,
    }).then(() => {
        watchPlotSize(plotDiv);
        resizePlot();
    });
}

export function drawPoints(points) {
    const normalized = points.map((point) => normalizePoint(point));
    const trace = createMarkerTrace(normalized, {
        name: 'Points',
        marker: {
            size: 10,
            color: COLORS.point,
            line: { color: COLORS.pointBorder, width: 1 },
        },
    });

    Plotly.react(PLOT_ID, trace ? [trace] : [], getBaseLayout(), { displayModeBar: false });
}

export function drawStep(points, stepData, context = {}) {
    if (!stepData) {
        return;
    }

    const normalizedPoints = points.map((point) => normalizePoint(point));
    const algorithm = context.algorithm || 'generic';

    const traces = [
        ...createBackgroundTrace(normalizedPoints),
        ...createOrderingTraces(normalizedPoints, stepData),
        ...createClusterTraces(normalizedPoints, stepData, algorithm),
        ...createBatchTrace(normalizedPoints, stepData),
        ...createActiveAreaTraces(normalizedPoints, stepData),
        ...createNeighborhoodTraces(normalizedPoints, stepData),
        ...createCentroidTrace(stepData),
    ].filter(Boolean);

    Plotly.react(PLOT_ID, traces, getBaseLayout(), { displayModeBar: false });
}

export function convertClickToPoint(event) {
    const plotDiv = document.getElementById(PLOT_ID);
    if (!plotDiv || !plotDiv._fullLayout) {
        return null;
    }

    const xaxis = plotDiv._fullLayout.xaxis;
    const yaxis = plotDiv._fullLayout.yaxis;
    const rect = plotDiv.getBoundingClientRect();
    const xPx = event.clientX - rect.left;
    const yPx = event.clientY - rect.top;
    const marginL = plotDiv._fullLayout.margin.l;
    const marginT = plotDiv._fullLayout.margin.t;

    const xVal = xaxis.p2d(xPx - marginL);
    const yVal = yaxis.p2d(yPx - marginT);

    if (xVal >= 0 && xVal <= 10 && yVal >= 0 && yVal <= 10) {
        return [xVal, yVal];
    }

    return null;
}
