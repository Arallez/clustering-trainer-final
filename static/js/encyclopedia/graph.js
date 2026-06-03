/**
 * Ontology Graph Visualizer using D3.js
 * Renders nodes (Concepts) and links (ConceptRelations) resembling Protege
 */

const GRAPH_POSITIONS_KEY = 'ontology_graph_positions';
const GRAPH_POSITIONS_VERSION = 'v1';

function syncGraphOverlayWithNavbar() {
    const page = document.querySelector('.graph-page-container');
    const navbar = document.querySelector('.navbar');
    if (!page || !navbar) return;

    const navbarRect = navbar.getBoundingClientRect();
    page.style.setProperty('--graph-navbar-bottom', `${Math.ceil(navbarRect.bottom)}px`);
}

function saveNodePositions(nodes) {
    try {
        const positions = {};
        nodes.forEach(n => {
            if (n.x !== undefined && n.y !== undefined) {
                positions[n.id] = { x: n.x, y: n.y };
            }
        });
        localStorage.setItem(GRAPH_POSITIONS_KEY, JSON.stringify({
            version: GRAPH_POSITIONS_VERSION,
            timestamp: Date.now(),
            positions: positions
        }));
    } catch (e) {
        console.warn('Could not save graph positions:', e);
    }
}

function loadNodePositions(nodes) {
    try {
        const saved = localStorage.getItem(GRAPH_POSITIONS_KEY);
        if (!saved) return false;
        
        const data = JSON.parse(saved);
        if (data.version !== GRAPH_POSITIONS_VERSION) return false;
        
        // Check if saved positions are for the same nodes
        const savedIds = Object.keys(data.positions);
        const currentIds = nodes.map(n => n.id);
        if (savedIds.length !== currentIds.length) return false;
        
        let hasAllPositions = true;
        nodes.forEach(n => {
            if (data.positions[n.id]) {
                n.x = data.positions[n.id].x;
                n.y = data.positions[n.id].y;
                n.fx = data.positions[n.id].x;
                n.fy = data.positions[n.id].y;
            } else {
                hasAllPositions = false;
            }
        });
        
        return hasAllPositions;
    } catch (e) {
        console.warn('Could not load graph positions:', e);
        return false;
    }
}

function initOntologyGraph(containerId, nodesData, linksData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Semantic Colors
    const colors = {
        1: '#3b82f6', // Algorithms (Blue)
        2: '#10b981', // Parameters (Green)
        3: '#f59e0b', // Metrics (Yellow)
        4: '#8b5cf6', // Use Cases (Purple)
        5: '#ec4899', // Geometry (Pink)
        6: '#14b8a6', // Scalability (Teal)
        7: '#f43f5e', // Cluster Size (Rose)
        8: '#64748b', // Inference Type (Slate)
        10: '#6366f1', // Quality Metrics (Indigo)
        11: '#06b6d4', // Quality Criteria / Conditions (Cyan)
        9: '#cbd5e1', // Default/Thing (Light Gray)
    };

    // Edge Styles Configuration
    const edgeStyles = {
        // Иерархия классов
        'IS_A': { color: '#94a3b8', dash: null },
        'PART_OF': { color: '#10b981', dash: '10, 5' },
        // Жёсткие связи — управляют доступностью задач и эффективным освоением
        'DEPENDS': { color: '#ef4444', dash: '6, 6' },
        'USES': { color: '#3b82f6', dash: '2, 4' },
        'EXTENDS': { color: '#f59e0b', dash: '6, 3' },
        'SPECIAL_CASE': { color: '#ec4899', dash: '4, 2' },
        // Мягкие связи — управляют ранжированием рекомендаций
        'RECOMMENDED_AFTER': { color: '#22c55e', dash: '10, 4' },
        'EVALUATED_BY': { color: '#06b6d4', dash: '8, 3' },
        // Структурные связи — все одним фиолетовым стилем
        'RELATED': { color: '#8b5cf6', dash: null },
        'HAS_PARAMETER': { color: '#8b5cf6', dash: null },
        'SOLVES_TASK': { color: '#8b5cf6', dash: null },
        'SUPPORTS_GEOMETRY': { color: '#8b5cf6', dash: null },
        'ASSUMES_CLUSTER_SIZE': { color: '#8b5cf6', dash: null },
        'HAS_SCALABILITY': { color: '#8b5cf6', dash: null },
        'HAS_INFERENCE_TYPE': { color: '#8b5cf6', dash: null },
        'ASSESSES_CRITERION': { color: '#8b5cf6', dash: null },
        'HELPS_SELECT_PARAMETER': { color: '#8b5cf6', dash: null },
        'default': { color: '#8b5cf6', dash: null }
    };

    // 1. REVERSE IS_A LINKS FOR VISUALIZATION
    linksData.forEach(l => {
        if (l.raw_type === 'IS_A') {
            const temp = l.source;
            l.source = l.target;
            l.target = temp;
        }
    });

    // 2. Calculate hierarchical depth
    nodesData.forEach(n => n.depth = 0);
    for (let i = 0; i < 15; i++) {
        linksData.forEach(l => {
            let s = typeof l.source === 'object' ? l.source : nodesData.find(n => n.id === l.source);
            let t = typeof l.target === 'object' ? l.target : nodesData.find(n => n.id === l.target);
            if (!s || !t) return;
            if (l.raw_type === 'IS_A') {
                if (t.depth <= s.depth) t.depth = s.depth + 1;
            }
        });
    }
    
    const infoPanel = d3.select("#graph-info-panel");
    let pinnedNode = null;
    let hoveredNode = null;
    let showOnlyLearned = false;
    let currentLayout = 'force';

    // Setup Filter Logic
    const filterToggle = document.getElementById('learned-filter-toggle');
    if (filterToggle) {
        filterToggle.addEventListener('change', (e) => {
            showOnlyLearned = e.target.checked;
            if (pinnedNode) clearPinnedNode(); // Only clear pinned node when filter is explicitly changed by user
            updateGraphVisibility();
        });
    }

    const svg = d3.select("#" + containerId)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const g = svg.append("g");

    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => g.attr("transform", event.transform));
    
    svg.call(zoom);
    
    d3.select("#btn-zoom-in").on("click", () => zoom.scaleBy(svg.transition().duration(300), 1.3));
    d3.select("#btn-zoom-out").on("click", () => zoom.scaleBy(svg.transition().duration(300), 1 / 1.3));
    d3.select("#btn-reset").on("click", () => {
        svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(0.8));
        clearPinnedNode();
    });

    const defs = svg.append("defs");
    Object.keys(edgeStyles).forEach(type => {
        const style = edgeStyles[type];
        defs.append("marker")
            .attr("id", `arrow-${type}`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 10)
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", style.color)
            .attr("d", "M0,-5L10,0L0,5");

        defs.append("marker")
            .attr("id", `arrow-${type}-muted`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 10)
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", style.color)
            .attr("fill-opacity", 0.12)
            .attr("d", "M0,-5L10,0L0,5");
            
        defs.append("marker")
            .attr("id", `arrow-${type}-hl`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 10)
            .attr("refY", 0)
            .attr("markerWidth", 10)
            .attr("markerHeight", 10)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", "#ffffff")
            .attr("d", "M0,-5L10,0L0,5");
    });

    // Node Glow filter for learned concepts
    const filter = defs.append("filter")
        .attr("id", "glow-learned")
        .attr("x", "-20%")
        .attr("y", "-20%")
        .attr("width", "140%")
        .attr("height", "140%");
    filter.append("feGaussianBlur")
        .attr("stdDeviation", "4")
        .attr("result", "blur");
    filter.append("feComposite")
        .attr("in", "SourceGraphic")
        .attr("in2", "blur")
        .attr("operator", "over");

    const classNodeIds = new Set(linksData.filter(l => l.raw_type === 'IS_A').map(l => l.source));
    nodesData.forEach(d => {
        d.isClass = classNodeIds.has(d.id) || d.id === 'root' || d.uri === 'Root_Clustering';
        d.rectWidth = Math.max(d.isClass ? 110 : 80, d.title.length * (d.isClass ? 8 : 7) + 20);
        d.rectHeight = d.isClass ? 32 : 26;
    });

    // Try to load saved positions
    const hasSavedPositions = loadNodePositions(nodesData);
    
    const simulation = d3.forceSimulation(nodesData)
        .force("link", d3.forceLink(linksData).id(d => d.id).distance(180))
        .velocityDecay(0.5); // Higher value = more damping = smoother movement
    
    // If we have saved positions, use lower alpha for quicker stabilization
    if (hasSavedPositions) {
        simulation.alpha(0.3);
    }

    const link = g.append("g")
        .attr("class", "links")
        .selectAll("path")
        .data(linksData)
        .enter().append("path")
        .attr("class", "link")
        .attr("fill", "none")
        .attr("stroke", d => (edgeStyles[d.raw_type] || edgeStyles['default']).color)
        .attr("stroke-dasharray", d => (edgeStyles[d.raw_type] || edgeStyles['default']).dash)
        .attr("marker-end", d => `url(#arrow-${d.raw_type || 'default'})`);

    const node = g.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(nodesData)
        .enter().append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    node.append("rect")
        .attr("width", d => d.rectWidth)
        .attr("height", d => d.rectHeight)
        .attr("x", d => -d.rectWidth / 2)
        .attr("y", d => -d.rectHeight / 2)
        .attr("fill", d => colors[d.group] || (d.isClass ? '#334155' : colors[9]))
        .attr("rx", d => d.isClass ? 16 : 4)
        .attr("ry", d => d.isClass ? 16 : 4)
        .attr("stroke", d => d.is_learned ? "#10b981" : "var(--bg-color)")
        .attr("stroke-width", d => d.is_learned ? "2px" : "1px")
        .style("filter", d => d.is_learned ? "url(#glow-learned)" : "none");

    node.append("text")
        .attr("dy", "0.35em")
        .style("font-weight", d => d.isClass ? "800" : "600")
        .style("font-size", d => d.isClass ? "12px" : "11px")
        .style("fill", "#ffffff")
        .style("text-shadow", "0px 1px 2px rgba(0,0,0,0.8)")
        .text(d => d.title);
    
    function updateGraphVisibility() {
        // Don't update if a node is highlighted (hovered or pinned)
        if (pinnedNode || hoveredNode) return;
        
        // Just updates visual opacity based on the showOnlyLearned filter.
        // It does NOT modify pinnedNode state anymore.
        node.transition().duration(300)
            .style("opacity", d => showOnlyLearned ? (d.is_learned ? 1 : 0.05) : 1)
            .style("pointer-events", d => showOnlyLearned ? (d.is_learned ? "all" : "none") : "all");

        link.transition().duration(300)
            .style("stroke-opacity", l => {
                if (currentLayout === 'tree' && l.raw_type !== 'IS_A') return 0.025;
                if (!showOnlyLearned) return 0.6;
                return (l.source.is_learned && l.target.is_learned) ? 0.6 : 0.02;
            })
            .attr("marker-end", l => {
                const type = l.raw_type || 'default';
                if (currentLayout === 'tree' && l.raw_type !== 'IS_A') return `url(#arrow-${type}-muted)`;
                if (!showOnlyLearned) return `url(#arrow-${type})`;
                return (l.source.is_learned && l.target.is_learned)
                    ? `url(#arrow-${type})`
                    : `url(#arrow-${type}-muted)`;
            });
    }

    function highlightNodeAndShowPanel(d, isPinned = false) {
        if (showOnlyLearned && !d.is_learned) return;

        const nodeElement = node.filter(n => n.id === d.id).node();
        
        // Interrupt any ongoing transitions to prevent conflicts
        node.interrupt();
        link.interrupt();
        
        // Reset others to base state (considering filter)
        node.select("rect")
            .attr("stroke", n => n.is_learned ? "#10b981" : "var(--bg-color)")
            .attr("stroke-width", n => n.is_learned ? "2px" : "1px");
        
        link.style("stroke-opacity", l => showOnlyLearned ? ((l.source.is_learned && l.target.is_learned) ? 0.6 : 0.02) : 0.6)
            .style("stroke-width", "2px")
            .style("stroke", l => (edgeStyles[l.raw_type] || edgeStyles['default']).color)
            .attr("marker-end", l => {
                const type = l.raw_type || 'default';
                if (!showOnlyLearned) return `url(#arrow-${type})`;
                return (l.source.is_learned && l.target.is_learned)
                    ? `url(#arrow-${type})`
                    : `url(#arrow-${type}-muted)`;
            });
            
        // Apply highlight
        d3.select(nodeElement).select("rect")
            .attr("stroke", "#ffffff")
            .attr("stroke-width", "3px");
        
        link.style("stroke-opacity", l => {
                if (showOnlyLearned && (!l.source.is_learned || !l.target.is_learned)) return 0.02;
                return (l.source.id === d.id || l.target.id === d.id) ? 1 : (showOnlyLearned ? 0.02 : 0.1);
            })
            .style("stroke-width", l => (l.source.id === d.id || l.target.id === d.id) ? "3px" : "2px")
            .style("stroke", l => (l.source.id === d.id || l.target.id === d.id) ? "#ffffff" : (edgeStyles[l.raw_type] || edgeStyles['default']).color)
            .attr("marker-end", l => {
                const type = l.raw_type || 'default';
                if (l.source.id === d.id || l.target.id === d.id) {
                    return `url(#arrow-${type}-hl)`;
                }
                return `url(#arrow-${type}-muted)`;
            });
        
        node.style("opacity", n => {
            if (showOnlyLearned && !n.is_learned) return 0.05;
            if (n.id === d.id) return 1;
            const isConnected = linksData.some(l => 
                (l.source.id === d.id && l.target.id === n.id) || 
                (l.target.id === d.id && l.source.id === n.id)
            );
            return isConnected ? 1 : 0.15;
        });

        let outgoing = linksData.filter(l => l.source.id === d.id).map(l => `
            <li ${showOnlyLearned && !l.target.is_learned ? 'style="opacity:0.4"' : ''}>
                <span class="panel-conn-type" style="color:${(edgeStyles[l.raw_type]||edgeStyles['default']).color}">▶ ${l.raw_type === 'IS_A' ? 'СОДЕРЖИТ' : l.type}</span>
                <span class="panel-conn-node">${(l.target.title || l.target.id)}</span>
            </li>
        `).join("");
        
        let incoming = linksData.filter(l => l.target.id === d.id).map(l => `
            <li ${showOnlyLearned && !l.source.is_learned ? 'style="opacity:0.4"' : ''}>
                <span class="panel-conn-type" style="color:${(edgeStyles[l.raw_type]||edgeStyles['default']).color}">◀ ${l.raw_type === 'IS_A' ? 'ЯВЛЯЕТСЯ' : l.type}</span>
                <span class="panel-conn-node">${(l.source.title || l.source.id)}</span>
            </li>
        `).join("");
        
        const pinHint = isPinned 
            ? `<div style="display:inline-flex; align-items:center; justify-content:center; background:rgba(96, 165, 250, 0.2); color:#60a5fa; padding:4px; border-radius:4px; margin-left:8px; border:1px solid rgba(96, 165, 250, 0.4);"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/></svg></div>` 
            : ``;
            
        const actionArea = isPinned
            ? (d.url ? `<a href="${d.url}" class="panel-action-btn" style="display:inline-flex; align-items:center; justify-content:center; gap:8px; text-align:center; background:#3b82f6; color:white; padding:10px 16px; border-radius:8px; text-decoration:none; margin-top:15px; font-weight:600; font-size:13px; transition:background 0.2s;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg> Открыть полную статью</a>` : '')
            : `<div style="margin-top: 25px; padding-top: 15px; border-top: 1px dashed rgba(255,255,255,0.1); text-align: center; color: #94a3b8; font-size: 11px; display:flex; align-items:center; justify-content:center; gap:6px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="7"/><path d="M12 6v4"/></svg>
                Кликните по узлу, чтобы закрепить панель
               </div>`;
        
        const uriText = d.uri ? d.uri.split('#').pop() : d.id;
        
        infoPanel.html(`
            <div class="panel-title" style="color:${colors[d.group]}; display:flex; align-items:center; justify-content:space-between;">
                <span>${d.title}</span>
                ${isPinned ? '<button id="close-panel-btn" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:16px;">✕</button>' : ''}
            </div>
            <div class="panel-uri" style="display:flex; align-items:center;">URI: ${uriText} ${pinHint}</div>

            ${(outgoing || incoming) ? `<div class="panel-section-title">Связи графа</div>` : ''}
            <ul class="panel-connections">
                ${outgoing}
                ${incoming}
            </ul>

            ${actionArea}
        `);
        
        infoPanel.classed("visible", true);
        
        if (isPinned) {
            const closeBtn = document.getElementById('close-panel-btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    clearPinnedNode();
                });
            }
        }
    }

    function clearPinnedNode() {
        pinnedNode = null;
        hoveredNode = null;
        
        // Interrupt any ongoing transitions
        node.interrupt();
        link.interrupt();
        
        node.select("rect")
            .attr("stroke", d => d.is_learned ? "#10b981" : "var(--bg-color)")
            .attr("stroke-width", d => d.is_learned ? "2px" : "1px");
        
        link.style("stroke-width", "2px")
            .style("stroke", l => (edgeStyles[l.raw_type] || edgeStyles['default']).color)
            .attr("marker-end", l => `url(#arrow-${l.raw_type || 'default'})`);
            
        updateGraphVisibility();
        infoPanel.classed("visible", false);
    }

    svg.on("click", function(event) {
        if (event.target.tagName === 'svg' || event.target.tagName === 'g') {
            clearPinnedNode();
        }
    });

    node.on("mouseover", function(event, d) {
        if (pinnedNode) return; // If pinned, don't change on hover
        // Set hoveredNode BEFORE calling highlight to prevent race conditions
        hoveredNode = d;
        highlightNodeAndShowPanel(d, false);
    })
    .on("mouseout", function(event, d) {
        if (pinnedNode) return; // If pinned, don't clear on hover out
        // Clear hoveredNode first, then clear highlight
        const wasHovered = hoveredNode;
        hoveredNode = null;
        if (wasHovered) clearPinnedNode();
    })
    .on("click", function(event, d) {
        if (event.defaultPrevented) return; // ignore drag
        event.stopPropagation(); // prevent svg click
        if (showOnlyLearned && !d.is_learned) return;
        
        if (pinnedNode && pinnedNode.id === d.id) {
            // Clicking the already pinned node unpins it
            clearPinnedNode();
        } else {
            // Pin the new node
            pinnedNode = d;
            highlightNodeAndShowPanel(d, true);
        }
    });

    function getIntersection(sx, sy, tx, ty, tWidth, tHeight, isClass) {
        const dx = tx - sx;
        const dy = ty - sy;
        if (dx === 0 && dy === 0) return {x: tx, y: ty};
        if (isClass) {
            const angle = Math.atan2(dy, dx);
            return {
                x: tx - Math.cos(angle) * (tWidth / 2),
                y: ty - Math.sin(angle) * (tHeight / 2)
            };
        }
        const hw = tWidth / 2;
        const hh = tHeight / 2;
        let ix, iy;
        if (Math.abs(dx) > 0) {
            ix = dx > 0 ? tx - hw : tx + hw;
            iy = ty - dy * (Math.abs(hw) / Math.abs(dx));
            if (iy < ty - hh) {
                iy = ty - hh;
                ix = tx - dx * (Math.abs(hh) / Math.abs(dy));
            } else if (iy > ty + hh) {
                iy = ty + hh;
                ix = tx - dx * (Math.abs(hh) / Math.abs(dy));
            }
        } else {
            ix = tx;
            iy = dy > 0 ? ty - hh : ty + hh;
        }
        return {x: ix, y: iy};
    }

    let saveTimeout = null;
    
    simulation.on("tick", () => {
        link.attr("d", d => {
            if (!d.source.x || !d.target.x) return "";
            const p = getIntersection(d.source.x, d.source.y, d.target.x, d.target.y, d.target.rectWidth, d.target.rectHeight, d.target.isClass);
            return `M${d.source.x},${d.source.y} L${p.x},${p.y}`;
        });
        node.attr("transform", d => `translate(${d.x},${d.y})`);
    });
    
    // Save positions when simulation ends
    simulation.on("end", () => {
        saveNodePositions(nodesData);
    });
    
    // Debounced save during simulation
    function debouncedSave() {
        if (saveTimeout) clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            saveNodePositions(nodesData);
        }, 500);
    }
    
    // Save positions when user leaves the page
    window.addEventListener('beforeunload', () => {
        saveNodePositions(nodesData);
    });
    
    // Save positions periodically during simulation
    const saveInterval = setInterval(() => {
        if (simulation.alpha() < 0.01) {
            clearInterval(saveInterval);
            return;
        }
        debouncedSave();
    }, 1000);

    function getNodeId(value) {
        return typeof value === 'object' ? value.id : value;
    }

    function computeHierarchyTargets() {
        const childrenByParent = new Map();
        const childIds = new Set();

        linksData.forEach(l => {
            if (l.raw_type !== 'IS_A') return;
            const parentId = getNodeId(l.source);
            const childId = getNodeId(l.target);
            if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, []);
            childrenByParent.get(parentId).push(childId);
            childIds.add(childId);
        });

        const rootCandidates = nodesData.filter(n => !childIds.has(n.id) && childrenByParent.has(n.id));
        const preferredRoot = rootCandidates.find(n =>
            n.id === 'root' ||
            (n.uri || '').includes('Root_Clustering') ||
            (n.title || '').toLowerCase().includes('кластериза')
        );
        const roots = preferredRoot
            ? [preferredRoot, ...rootCandidates.filter(n => n.id !== preferredRoot.id)]
            : rootCandidates;

        const visited = new Set();
        const ordered = [];
        const orderById = new Map();
        const queue = roots.map((node, index) => ({ node, depth: 0, parentOrder: index }));

        while (queue.length > 0) {
            const item = queue.shift();
            if (!item.node || visited.has(item.node.id)) continue;

            visited.add(item.node.id);
            ordered.push(item);
            orderById.set(item.node.id, ordered.length - 1);

            const childNodes = (childrenByParent.get(item.node.id) || [])
                .map(id => nodesData.find(n => n.id === id))
                .filter(Boolean)
                .sort((a, b) => (a.title || '').localeCompare(b.title || ''));

            childNodes.forEach(child => {
                queue.push({
                    node: child,
                    depth: item.depth + 1,
                    parentOrder: orderById.get(item.node.id) || 0
                });
            });
        }

        nodesData.forEach(node => {
            if (!visited.has(node.id)) {
                ordered.push({
                    node,
                    depth: Math.max(1, node.depth || 1),
                    parentOrder: ordered.length
                });
            }
        });

        const levels = d3.group(ordered, d => d.depth);
        const maxDepth = d3.max(ordered, d => d.depth) || 1;
        const nodeSpacing = 155;
        const layerHeight = 115;
        const rowGap = 44;
        const maxColumns = Math.max(6, Math.floor(Math.max(width * 1.25, 1100) / nodeSpacing));

        levels.forEach((items, depth) => {
            const sorted = items.sort((a, b) =>
                (a.parentOrder - b.parentOrder) ||
                (a.node.title || '').localeCompare(b.node.title || '')
            );
            const rows = Math.ceil(sorted.length / maxColumns);

            sorted.forEach((item, index) => {
                const row = Math.floor(index / maxColumns);
                const col = index % maxColumns;
                const columnsInRow = Math.min(maxColumns, sorted.length - row * maxColumns);

                item.node.treeX = (col - (columnsInRow - 1) / 2) * nodeSpacing;
                item.node.treeY = (depth - maxDepth / 2) * layerHeight + (row - (rows - 1) / 2) * rowGap;
            });
        });
    }

    window.applyGraphLayout = function(type) {
        currentLayout = type;
        // Clear saved positions when changing layout
        localStorage.removeItem(GRAPH_POSITIONS_KEY);
        
        // Unfix all nodes so they can move freely
        nodesData.forEach(n => {
            n.fx = null;
            n.fy = null;
            n.vx = 0;
            n.vy = 0;
        });
        
        simulation.force("x", null);
        simulation.force("y", null);
        simulation.force("r", null);
        simulation.force("center", null);

        let maxDepth = d3.max(nodesData, d => d.depth) || 1;
        const forceLinks = type === 'tree' ? linksData.filter(l => l.raw_type === 'IS_A') : linksData;
        if (type === 'tree') computeHierarchyTargets();
        simulation.force("link", d3.forceLink(forceLinks).id(d => d.id).distance(type === 'tree' ? 80 : 180));

        if (type === 'force') {
            simulation
                .force("charge", d3.forceManyBody().strength(-800))
                .force("center", d3.forceCenter(0, 0).strength(0.5))
                .force("collide", d3.forceCollide().radius(d => d.rectWidth / 2 + 30).iterations(2));
        } else if (type === 'tree') {
            simulation
                .force("charge", d3.forceManyBody().strength(-90))
                .force("y", d3.forceY(d => d.treeY || 0).strength(0.95))
                .force("x", d3.forceX(d => d.treeX || 0).strength(0.9))
                .force("collide", d3.forceCollide().radius(d => d.rectWidth / 2 + 18).iterations(2));
        } else if (type === 'radial') {
            const radiusStep = 150;
            simulation
                .force("charge", d3.forceManyBody().strength(-500))
                .force("r", d3.forceRadial(d => d.depth * radiusStep, 0, 0).strength(0.8))
                .force("collide", d3.forceCollide().radius(d => d.rectWidth / 2 + 25).iterations(3));
        }

        updateGraphVisibility();
        
        // Use lower alpha for smoother transition instead of full restart
        simulation
            .velocityDecay(type === 'tree' ? 0.72 : 0.58)
            .alpha(type === 'tree' ? 0.24 : 0.38)
            .alphaDecay(type === 'tree' ? 0.024 : 0.018)
            .alphaMin(0.01)
            .restart();
        svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(type === 'tree' ? 0.65 : 0.5));
    };

    window.applyGraphLayout('force');

    document.querySelectorAll('.toolbar-btn').forEach(btn => {
        var newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        newBtn.addEventListener('click', function() {
            document.querySelectorAll('.toolbar-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            window.applyGraphLayout(this.getAttribute('data-layout'));
        });
    });

    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function tryInitGraph() {
    if (typeof d3 === "undefined") return false;
    const data = window.ONTOLOGY_GRAPH_DATA;
    if (!data || !data.nodes || !data.links) return false;
    const container = document.getElementById("ontology-graph");
    if (!container) return false;
    if (container.children.length > 0) return true;
    if (container.clientWidth === 0 || container.clientHeight === 0) return false;
    initOntologyGraph("ontology-graph", data.nodes, data.links);
    return true;
}

function waitForD3AndInit() {
    let attempts = 0;
    const interval = setInterval(() => {
        attempts++;
        if (tryInitGraph()) {
            clearInterval(interval);
        } else if (attempts > 50) {
            clearInterval(interval);
            console.error("Failed to initialize ontology graph (D3 missing or container hidden).");
        }
    }, 100);
}

// Read graph data from JSON script tag
function loadGraphData() {
    const dataEl = document.getElementById('graph-data');
    if (dataEl) {
        try {
            window.ONTOLOGY_GRAPH_DATA = JSON.parse(dataEl.textContent);
        } catch (e) {
            console.error('Failed to parse graph data:', e);
        }
    }
}

// Mobile Legend Modal functionality
function initLegendModal() {
    const legendToggleBtn = document.getElementById('legend-toggle-btn');
    const legendModal = document.getElementById('legend-modal');
    const legendModalClose = document.getElementById('legend-modal-close');
    
    if (!legendToggleBtn || !legendModal || !legendModalClose) return;
    
    // Open modal
    legendToggleBtn.addEventListener('click', () => {
        legendModal.classList.add('visible');
        document.body.style.overflow = 'hidden';
    });
    
    // Close modal on button click
    legendModalClose.addEventListener('click', () => {
        legendModal.classList.remove('visible');
        document.body.style.overflow = '';
    });
    
    // Close modal on backdrop click
    legendModal.addEventListener('click', (e) => {
        if (e.target === legendModal) {
            legendModal.classList.remove('visible');
            document.body.style.overflow = '';
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && legendModal.classList.contains('visible')) {
            legendModal.classList.remove('visible');
            document.body.style.overflow = '';
        }
    });
    
    // Sync mobile filter toggle with desktop toggle
    const mobileFilterToggle = document.getElementById('learned-filter-toggle-mobile');
    const desktopFilterToggle = document.getElementById('learned-filter-toggle');
    
    if (mobileFilterToggle && desktopFilterToggle) {
        mobileFilterToggle.addEventListener('change', (e) => {
            desktopFilterToggle.checked = e.target.checked;
            desktopFilterToggle.dispatchEvent(new Event('change'));
        });
        
        // Also sync from desktop to mobile
        desktopFilterToggle.addEventListener('change', (e) => {
            mobileFilterToggle.checked = e.target.checked;
        });
    }
}

// Info Panel Backdrop functionality for mobile
function initInfoPanelBackdrop() {
    const infoPanelBackdrop = document.getElementById('info-panel-backdrop');
    const infoPanel = document.getElementById('graph-info-panel');
    
    if (!infoPanelBackdrop || !infoPanel) return;
    
    // Observer to watch for visible class on info panel
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                const isVisible = infoPanel.classList.contains('visible');
                if (isVisible) {
                    infoPanelBackdrop.classList.add('visible');
                } else {
                    infoPanelBackdrop.classList.remove('visible');
                }
            }
        });
    });
    
    observer.observe(infoPanel, { attributes: true });
    
    // Close info panel when clicking backdrop
    infoPanelBackdrop.addEventListener('click', () => {
        infoPanel.classList.remove('visible');
    });
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", function() {
        syncGraphOverlayWithNavbar();
        loadGraphData();
        waitForD3AndInit();
        initLegendModal();
        initInfoPanelBackdrop();
        window.addEventListener('resize', syncGraphOverlayWithNavbar);
    });
} else {
    syncGraphOverlayWithNavbar();
    loadGraphData();
    waitForD3AndInit();
    initLegendModal();
    initInfoPanelBackdrop();
    window.addEventListener('resize', syncGraphOverlayWithNavbar);
}
