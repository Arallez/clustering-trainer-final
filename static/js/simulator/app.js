import {
    runKMeans,
    runMiniBatch,
    runDBSCAN,
    runForel,
    runAgglomerative,
    runWard,
    runMeanShift,
    generatePreset,
    getDendrogram,
    runGMM,
    runSpectral,
    runOPTICS,
    runAffinityPropagation,
    runBisecting,
    runBIRCH,
} from './api.js?v=8.1';
import { initPlot, drawPoints, drawStep, convertClickToPoint, resizePlot } from './plot.js?v=7.1';

const { createApp, ref, onMounted, onBeforeUnmount, watch, nextTick } = Vue;

const AGGLOMERATIVE_LABELS = {
    single: 'Одиночная',
    complete: 'Полная',
    average: 'Средняя',
};

const DENDROGRAM_TITLES = {
    agglomerative: 'Дендрограмма (агломеративная)',
    ward: 'Дендрограмма (Уорд)',
    bisecting: 'Дендрограмма (Bisecting K-Means)',
    birch: 'Дендрограмма (BIRCH)',
};

const SUPPORTED_ALGORITHMS = new Set([
    'kmeans',
    'minibatch',
    'dbscan',
    'forel',
    'agglomerative',
    'ward',
    'meanshift',
    'gmm',
    'spectral',
    'optics',
    'affinity',
    'bisecting',
    'birch',
]);

function getInitialAlgorithm() {
    const algorithmFromQuery = new URLSearchParams(window.location.search).get('algorithm');
    if (algorithmFromQuery && SUPPORTED_ALGORITHMS.has(algorithmFromQuery)) {
        return algorithmFromQuery;
    }
    return 'kmeans';
}

function getInitialPreset() {
    const presetFromQuery = new URLSearchParams(window.location.search).get('preset');
    const supportedPresets = new Set([
        'moons',
        'circles',
        'blobs',
        'grid',
        'hierarchy',
        'dense_sparse',
        'anisotropic',
        'outliers',
        'many_blobs',
        'bridge'
    ]);
    return supportedPresets.has(presetFromQuery) ? presetFromQuery : '';
}

const app = createApp({
    setup() {
        const algorithm = ref(getInitialAlgorithm());
        const k = ref(3);
        const eps = ref(1.0);
        const minPts = ref(3);
        const radius = ref(1.0);
        const bandwidth = ref(1.0);
        const sigma = ref(1.0);
        const damping = ref(0.5);
        const xi = ref(0.05);
        const threshold = ref(0.5);
        const agglomerativeLinkage = ref('average');
        const batchSize = ref(24);
        const playbackSpeed = ref(900);
        const points = ref([]);
        const history = ref([]);
        const currentStep = ref(0);
        const isRunning = ref(false);
        const isPlaying = ref(false);
        const selectedPreset = ref(getInitialPreset());
        const showDendrogram = ref(false);
        const cachedDendrogram = ref(null);
        const sidebarOpen = ref(false);
        const simulatorProgressMessage = ref('');

        let playbackTimer = null;

        const getCurrentStepData = () => history.value[currentStep.value] || null;

        const showServerError = (error) => {
            console.error(error);
            alert('Ошибка сервера');
        };

        const stopPlayback = () => {
            if (playbackTimer) {
                clearInterval(playbackTimer);
                playbackTimer = null;
            }
            isPlaying.value = false;
        };

        const redrawCurrentStep = () => {
            const step = getCurrentStepData();
            if (history.value.length > 0 && step) {
                drawStep(points.value, step, { algorithm: algorithm.value });
            } else {
                drawPoints(points.value);
            }
        };

        const startPlayback = () => {
            if (history.value.length <= 1) {
                return;
            }

            stopPlayback();
            isPlaying.value = true;
            playbackTimer = setInterval(() => {
                if (currentStep.value >= history.value.length - 1) {
                    stopPlayback();
                    return;
                }
                currentStep.value += 1;
            }, Number(playbackSpeed.value));
        };

        const togglePlayback = () => {
            if (isPlaying.value) {
                stopPlayback();
                return;
            }

            if (currentStep.value >= history.value.length - 1) {
                currentStep.value = 0;
            }
            startPlayback();
        };

        const handleCanvasClick = (event) => {
            if (history.value.length > 0) {
                return;
            }

            const point = convertClickToPoint(event);
            if (point) {
                points.value.push(point);
                drawPoints(points.value);
            }
        };

        const clearPoints = () => {
            stopPlayback();
            points.value = [];
            history.value = [];
            currentStep.value = 0;
            selectedPreset.value = '';
            cachedDendrogram.value = null;
            simulatorProgressMessage.value = '';
            initPlot();
        };

        const loadPreset = async () => {
            if (!selectedPreset.value) {
                return;
            }

            isRunning.value = true;
            try {
                const data = await generatePreset(selectedPreset.value, 100);
                if (!data.success) {
                    alert(`Ошибка загрузки пресета: ${data.error}`);
                    return;
                }

                stopPlayback();
                points.value = data.points;
                history.value = [];
                currentStep.value = 0;
                cachedDendrogram.value = null;
                drawPoints(points.value);
            } catch (error) {
                showServerError(error);
            } finally {
                isRunning.value = false;
            }
        };

        const storeHistory = (data) => {
            stopPlayback();
            history.value = data.history || [];
            currentStep.value = 0;
            const lastStep = history.value[history.value.length - 1];
            cachedDendrogram.value = lastStep && lastStep.dendrogram ? lastStep.dendrogram : null;
            nextTick(() => {
                resizePlot();
                redrawCurrentStep();
            });
        };

        const runAlgorithm = async () => {
            isRunning.value = true;
            try {
                let data = null;

                switch (algorithm.value) {
                case 'kmeans':
                    data = await runKMeans(points.value, k.value);
                    break;
                case 'minibatch':
                    data = await runMiniBatch(points.value, k.value, batchSize.value);
                    break;
                case 'dbscan':
                    data = await runDBSCAN(points.value, Number.parseFloat(eps.value), minPts.value);
                    break;
                case 'forel':
                    data = await runForel(points.value, Number.parseFloat(radius.value));
                    break;
                case 'agglomerative':
                    data = await runAgglomerative(points.value, k.value, agglomerativeLinkage.value);
                    break;
                case 'ward':
                    data = await runWard(points.value, k.value);
                    break;
                case 'meanshift':
                    data = await runMeanShift(points.value, Number.parseFloat(bandwidth.value));
                    break;
                case 'gmm':
                    data = await runGMM(points.value, k.value);
                    break;
                case 'spectral':
                    data = await runSpectral(points.value, k.value, Number.parseFloat(sigma.value));
                    break;
                case 'optics':
                    data = await runOPTICS(points.value, minPts.value, Number.parseFloat(xi.value));
                    break;
                case 'affinity':
                    data = await runAffinityPropagation(points.value, Number.parseFloat(damping.value));
                    break;
                case 'bisecting':
                    data = await runBisecting(points.value, k.value);
                    break;
                case 'birch':
                    data = await runBIRCH(points.value, Number.parseFloat(threshold.value), k.value);
                    break;
                default:
                    data = { success: false, error: `Неизвестный алгоритм: ${algorithm.value}` };
                }

                if (!data || !data.success) {
                    alert(`Ошибка: ${data ? data.error : 'Неизвестная ошибка'}`);
                    return;
                }

                storeHistory(data);
                if (data.simulator_progress && data.simulator_progress.completed) {
                    simulatorProgressMessage.value = 'Симуляторный шаг засчитан в учебном маршруте.';
                } else {
                    simulatorProgressMessage.value = '';
                }
            } catch (error) {
                showServerError(error);
            } finally {
                isRunning.value = false;
            }
        };

        const renderDendrogram = (dendroData, algo = 'agglomerative', options = {}) => {
            const traces = (dendroData.icoord || []).map((coords, index) => ({
                x: coords,
                y: dendroData.dcoord[index],
                mode: 'lines',
                line: { color: '#6366f1', width: 2 },
                showlegend: false,
                hoverinfo: 'skip',
            }));

            const titleText = algo === 'agglomerative'
                ? `${DENDROGRAM_TITLES[algo]}: ${AGGLOMERATIVE_LABELS[options.linkage] || AGGLOMERATIVE_LABELS.average}`
                : (DENDROGRAM_TITLES[algo] || 'Dendrogram');

            const layout = {
                title: {
                    text: titleText,
                    font: { color: '#fafaf9', size: 18, family: "'Space Grotesk', sans-serif" },
                },
                paper_bgcolor: '#1c1917',
                plot_bgcolor: '#1c1917',
                font: { color: '#a8a29e', family: "'Space Grotesk', sans-serif" },
                margin: { t: 50, b: 50, l: 60, r: 20 },
                xaxis: {
                    showgrid: false,
                    zeroline: false,
                    showticklabels: false,
                    title: { text: 'Точки', font: { color: '#a8a29e' } },
                },
                yaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(255,255,255,0.06)',
                    zeroline: false,
                    title: { text: 'Расстояние', font: { color: '#a8a29e' } },
                    tickfont: { color: '#d6d3d1' },
                },
            };

            Plotly.newPlot('dendrogram-plot', traces, layout, { responsive: true, displayModeBar: false });
        };

        const viewDendrogram = async () => {
            if (points.value.length < 2) {
                alert('Нужно минимум 2 точки для дендрограммы');
                return;
            }

            if ((algorithm.value === 'bisecting' || algorithm.value === 'birch') && cachedDendrogram.value) {
                showDendrogram.value = true;
                setTimeout(() => {
                    renderDendrogram(cachedDendrogram.value, algorithm.value);
                }, 100);
                return;
            }

            const options = {};
            if (algorithm.value === 'agglomerative') {
                options.linkage = agglomerativeLinkage.value;
            }
            if (algorithm.value === 'birch') {
                options.threshold = Number.parseFloat(threshold.value);
            }

            isRunning.value = true;
            try {
                const data = await getDendrogram(points.value, algorithm.value, options);
                if (!data.success) {
                    alert(`Ошибка: ${data.error}`);
                    return;
                }

                showDendrogram.value = true;
                setTimeout(() => {
                    renderDendrogram(data.dendrogram, algorithm.value, options);
                }, 100);
            } catch (error) {
                showServerError(error);
            } finally {
                isRunning.value = false;
            }
        };

        const closeDendrogram = () => {
            showDendrogram.value = false;
        };

        const nextStep = () => {
            stopPlayback();
            if (currentStep.value < history.value.length - 1) {
                currentStep.value += 1;
            }
        };

        const prevStep = () => {
            stopPlayback();
            if (currentStep.value > 0) {
                currentStep.value -= 1;
            }
        };

        const goToFirstStep = () => {
            stopPlayback();
            currentStep.value = 0;
        };

        const goToLastStep = () => {
            stopPlayback();
            currentStep.value = Math.max(history.value.length - 1, 0);
        };

        watch(currentStep, () => {
            redrawCurrentStep();
            if (currentStep.value >= history.value.length - 1) {
                stopPlayback();
            }
        });

        watch(algorithm, () => {
            clearPoints();
        });

        watch(selectedPreset, () => {
            if (selectedPreset.value) {
                loadPreset();
            }
        });

        watch(playbackSpeed, () => {
            if (isPlaying.value) {
                startPlayback();
            }
        });

        onMounted(() => {
            setTimeout(() => {
                initPlot();
                if (selectedPreset.value) {
                    loadPreset();
                }
            }, 100);
        });

        onBeforeUnmount(() => {
            stopPlayback();
        });

        return {
            algorithm,
            k,
            eps,
            minPts,
            radius,
            bandwidth,
            sigma,
            damping,
            xi,
            threshold,
            agglomerativeLinkage,
            batchSize,
            playbackSpeed,
            points,
            history,
            currentStep,
            isRunning,
            isPlaying,
            selectedPreset,
            showDendrogram,
            simulatorProgressMessage,
            sidebarOpen,
            handleCanvasClick,
            clearPoints,
            runAlgorithm,
            viewDendrogram,
            closeDendrogram,
            nextStep,
            prevStep,
            togglePlayback,
            goToFirstStep,
            goToLastStep,
        };
    },
});

app.mount('#app');
