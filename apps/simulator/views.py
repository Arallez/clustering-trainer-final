import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from .algorithms import (
    kmeans_step,
    dbscan_step,
    forel_step,
    agglomerative_step,
    ward_step,
    mean_shift_step,
    compute_dendrogram_data,
    gmm_step,
    spectral_step,
    optics_step,
    affinity_propagation_step,
    bisecting_kmeans_step,
    birch_step,
    compute_bisecting_dendrogram,
    compute_birch_dendrogram,
    minibatch_kmeans_step,
    to_python_types,
)
from .catalog import AGGLOMERATIVE_LINKAGES
from .models import SimulatorProgress
from .presets import generate_preset


def _record_simulator_progress(request, algorithm, preset, module_slug):
    if not request.user.is_authenticated or not module_slug:
        return None

    now = timezone.now()
    progress, created = SimulatorProgress.objects.get_or_create(
        user=request.user,
        module_slug=module_slug,
        algorithm=algorithm,
        preset=preset or '',
        defaults={
            'first_run_at': now,
            'last_run_at': now,
            'completed_at': now,
            'run_count': 1,
        },
    )
    if not created:
        update_fields = ['last_run_at', 'completed_at', 'run_count']
        if not progress.first_run_at:
            progress.first_run_at = now
            update_fields.append('first_run_at')
        progress.last_run_at = now
        progress.completed_at = progress.completed_at or now
        progress.run_count += 1
        progress.save(update_fields=update_fields)

    return {
        'completed': True,
        'module_slug': progress.module_slug,
        'algorithm': progress.algorithm,
        'preset': progress.preset,
        'run_count': progress.run_count,
    }


@ensure_csrf_cookie
def index(request):
    """Страница симулятора (песочница: точки + алгоритмы)."""
    return render(request, 'simulator/index.html')


def _redirect_legacy_challenge(request, slug):
    """Редирект со старого /simulator/challenge/<slug>/ на /tasks/challenge/<slug>/."""
    return redirect(reverse('tasks:challenge_detail', kwargs={'slug': slug}), permanent=False)


# --- API Endpoints ---

def get_preset(request):
    """
    Returns points for a selected preset (Blobs, Moons, etc.)
    """
    if request.method == 'GET':
        try:
            # Get params (frontend sends 'name', keeping 'preset' for backward compat)
            preset_name = request.GET.get('name') or request.GET.get('preset') or 'blobs'
            
            # Generate 300 points by default for the simulator
            data = generate_preset(preset_name, n_samples=300)
            
            return JsonResponse({'success': True, 'points': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

def run_algorithm(request):
    """Unified endpoint for running all clustering algorithms"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            algo = data.get('algorithm')
            points = data.get('points', [])
            params = data.get('params', {})
            
            history = []
            
            if algo == 'kmeans':
                k = int(params.get('k', 3))
                history = kmeans_step(points, k)
            elif algo == 'dbscan':
                eps = float(params.get('eps', 0.5))
                min_pts = int(params.get('minPts', 3))
                history = dbscan_step(points, eps, min_pts)
            elif algo == 'forel':
                r = float(params.get('radius', 1.0))
                history = forel_step(points, r)
            elif algo == 'agglomerative':
                k = int(params.get('k', 2))
                linkage_method = params.get('linkage', 'average')
                if linkage_method not in AGGLOMERATIVE_LINKAGES:
                    raise ValueError(f'Unsupported agglomerative linkage: {linkage_method}')
                history = agglomerative_step(points, k, linkage_method=linkage_method)
            elif algo == 'ward':
                k = int(params.get('k', 2))
                history = ward_step(points, k)
            elif algo == 'meanshift':
                bandwidth = float(params.get('bandwidth', 1.0))
                history = mean_shift_step(points, bandwidth)
            # New algorithms
            elif algo == 'gmm':
                n_components = int(params.get('n_components', 3))
                history = gmm_step(points, n_components)
            elif algo == 'spectral':
                n_clusters = int(params.get('k', 3))
                sigma = float(params.get('sigma', 1.0))
                history = spectral_step(points, n_clusters, sigma)
            elif algo == 'optics':
                min_pts = int(params.get('minPts', 5))
                xi = float(params.get('xi', 0.05))
                history = optics_step(points, min_pts, xi)
            elif algo == 'affinity':
                damping = float(params.get('damping', 0.5))
                history = affinity_propagation_step(points, damping)
            elif algo == 'bisecting':
                n_clusters = int(params.get('k', 3))
                history = bisecting_kmeans_step(points, n_clusters)
            elif algo == 'birch':
                threshold = float(params.get('threshold', 0.5))
                n_clusters = int(params.get('k', 3))
                history = birch_step(points, threshold, n_clusters=n_clusters)
            elif algo == 'minibatch':
                k = int(params.get('k', 3))
                batch_size = int(params.get('batchSize', 24))
                history = minibatch_kmeans_step(points, k, batch_size=batch_size)
            else:
                return JsonResponse({'success': False, 'error': f'Unknown algorithm: {algo}'})

            history = to_python_types(history)

            simulator_progress = _record_simulator_progress(
                request,
                algorithm=algo,
                preset=data.get('preset') or params.get('preset') or '',
                module_slug=data.get('module_slug') or data.get('module') or '',
            )
            response_data = {'success': True, 'history': history}
            if simulator_progress:
                response_data['simulator_progress'] = simulator_progress
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

def get_dendrogram(request):
    """
    Returns dendrogram data for plotting.
    Supports different algorithms via 'algorithm' parameter.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            algorithm = data.get('algorithm', 'agglomerative')
            
            if algorithm == 'bisecting':
                ddata = compute_bisecting_dendrogram(points)
            elif algorithm == 'birch':
                threshold = float(data.get('threshold', 0.5))
                ddata = compute_birch_dendrogram(points, threshold)
            elif algorithm == 'ward':
                ddata = compute_dendrogram_data(points, linkage_method='ward')
            elif algorithm == 'agglomerative':
                linkage_method = data.get('linkage', 'average')
                if linkage_method not in AGGLOMERATIVE_LINKAGES:
                    raise ValueError(f'Unsupported agglomerative linkage: {linkage_method}')
                ddata = compute_dendrogram_data(points, linkage_method=linkage_method)
            else:
                return JsonResponse({'success': False, 'error': f'Unknown dendrogram algorithm: {algorithm}'})
            
            if 'error' in ddata:
                return JsonResponse({'success': False, 'error': ddata['error']})
            
            return JsonResponse({'success': True, 'dendrogram': ddata})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})
