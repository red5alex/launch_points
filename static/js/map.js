// Leaflet map initialization
let map;
let layers = {};
let selectedSections = new Set();

document.addEventListener('DOMContentLoaded', function() {
    // Check if map container exists
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('Map container #map not found!');
        return;
    }
    
    console.log('Initializing map...');
    // Initialize map (default to Berlin)
    map = L.map('map').setView([52.5200, 13.4050], 11);
    console.log('Map initialized at:', map.getCenter());

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Initialize layer groups
    layers.launchPoints = L.layerGroup().addTo(map);
    layers.pois = L.layerGroup().addTo(map);
    layers.routeSections = L.layerGroup().addTo(map);
    layers.waypoints = L.layerGroup().addTo(map);
    layers.stations = L.layerGroup().addTo(map);
    layers.walkPaths = L.layerGroup().addTo(map);

    // Load all GeoJSON layers
    loadGeoJSONLayers();

    // Handle region navigation
    document.querySelectorAll('.region-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const bounds = this.dataset.bounds.split(',').map(Number);
            // bounds format: [minx, miny, maxx, maxy] -> convert to [[south, west], [north, east]]
            map.fitBounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]]);
        });
    });
});

function getStatusColor(status) {
    // Return color based on status
    if (status === 'pending') {
        return '#ff9999';  // Light red for pending
    }
    return null;  // Default color for approved
}

function loadGeoJSONLayers() {
    // Load launch points
    fetch('/api/launch-points/geojson/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Launch points loaded:', data);
            
            // API should return a FeatureCollection directly
            if (!data || !data.type || data.type !== 'FeatureCollection') {
                console.error('Unexpected data format - expected FeatureCollection:', data);
                return;
            }
            
            if (!data.features || !Array.isArray(data.features)) {
                console.error('Features is not an array:', data.features);
                return;
            }
            
            if (data.features.length === 0) {
                console.warn('No launch points found');
                return;
            }
            
            console.log('Processing', data.features.length, 'launch point features using L.geoJSON');
            
            // Use the FeatureCollection directly
            const featureCollection = data;
            
            const geoJsonLayer = L.geoJSON(featureCollection, {
                pointToLayer: function(feature, latlng) {
                    // feature should have properties and geometry at this point
                    const props = feature.properties || {};
                    const status = props.status || 'approved';
                    const accessibility = props.accessibility || 'good';
                    const isPending = status === 'pending';
                    
                    // Color based on accessibility
                    let color = 'blue';
                    if (accessibility === 'good') color = 'green';
                    else if (accessibility === 'moderate') color = 'orange';
                    else if (accessibility === 'poor') color = 'red';
                    
                    // For pending, use a different color
                    if (isPending) {
                        color = 'violet';
                    }
                    
                    // Create marker with colored icon
                    const iconUrl = `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${color}.png`;
                    
                    return L.marker(latlng, {
                        icon: L.icon({
                            iconUrl: iconUrl,
                            shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
                            iconSize: [25, 41],
                            iconAnchor: [12, 41],
                            popupAnchor: [1, -34],
                            shadowSize: [41, 41]
                        })
                    });
                },
                onEachFeature: function(feature, layer) {
                    const props = feature.properties || {};
                    const name = props.name || 'Unnamed';
                    const status = props.status || 'approved';
                    const statusText = status === 'pending' ? ' (Pending)' : '';
                    layer.bindPopup(`<strong>${name}${statusText}</strong>`);
                    layer.on('click', function() {
                        loadLaunchPointInfo(props.id || feature.id);
                    });
                }
            });
            
            geoJsonLayer.addTo(layers.launchPoints);
            const addedCount = geoJsonLayer.getLayers().length;
            console.log('Launch points processing complete:', addedCount, 'markers added to map');
            
            // Fit map to show all markers
            if (addedCount > 0) {
                setTimeout(function() {
                    const actualCount = layers.launchPoints.getLayers().length;
                    console.log('Launch points layer group contains', actualCount, 'markers');
                    
                    // Fit map to show all markers using the GeoJSON layer bounds
                    try {
                        const bounds = geoJsonLayer.getBounds();
                        if (bounds && bounds.isValid()) {
                            map.fitBounds(bounds, { padding: [50, 50] });
                            console.log('Fitted map to bounds containing', actualCount, 'markers');
                        } else {
                            console.warn('Invalid bounds from GeoJSON layer, trying fallback');
                            // Fallback: collect positions manually
                            const latlngs = [];
                            layers.launchPoints.eachLayer(function(layer) {
                                if (layer.getLatLng) {
                                    latlngs.push(layer.getLatLng());
                                }
                            });
                            if (latlngs.length > 0) {
                                const fallbackBounds = L.latLngBounds(latlngs);
                                map.fitBounds(fallbackBounds, { padding: [50, 50] });
                                console.log('Fitted map using fallback method');
                            }
                        }
                    } catch (error) {
                        console.error('Error fitting bounds:', error);
                    }
                }, 100);
            } else {
                console.warn('No markers were added - check feature structure above');
            }
        })
        .catch(error => {
            console.error('Error loading launch points:', error);
            console.error('URL attempted:', '/api/launch-points/geojson/');
        });

    // Load POIs
    fetch('/api/pois/geojson/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('POIs loaded:', data);
            if (!data || !data.type || data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
                console.error('Unexpected POIs data format:', data);
                return;
            }
            if (data.features.length === 0) {
                console.warn('No POIs found');
                return;
            }
            L.geoJSON(data, {
                pointToLayer: function(feature, latlng) {
                    const status = feature.properties.status;
                    const isPending = status === 'pending';
                    
                    // Use different icon for POIs, lighter if pending
                    const iconColor = isPending ? '#ff9999' : '#3388ff';
                    
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'poi-marker',
                            html: `<i class="fa-solid fa-map-pin" style="color: ${iconColor}; font-size: 24px;"></i>`,
                            iconSize: [24, 24],
                            iconAnchor: [12, 24]
                        })
                    });
                },
                onEachFeature: function(feature, layer) {
                    const name = feature.properties.name;
                    const poiType = feature.properties.poi_type_name || 'POI';
                    const status = feature.properties.status;
                    const statusText = status === 'pending' ? ' (Pending)' : '';
                    layer.bindPopup(`<strong>${name}</strong><br>Type: ${poiType}${statusText}`);
                    layer.on('click', function() {
                        loadPOIInfo(feature.properties.id);
                    });
                }
            }).addTo(layers.pois);
        })
        .catch(error => console.error('Error loading POIs:', error));

    // Load route sections
    fetch('/api/route-sections/geojson/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Route sections loaded:', data);
            if (!data || !data.type || data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
                console.error('Unexpected route sections data format:', data);
                return;
            }
            if (data.features.length === 0) {
                console.warn('No route sections found');
                return;
            }
            
            // Debug: Check first feature structure
            if (data.features.length > 0) {
                console.log('First route section feature:', data.features[0]);
                console.log('First feature ID (feature.id):', data.features[0].id);
                console.log('First feature properties:', data.features[0].properties);
                console.log('First feature properties.id:', data.features[0].properties ? data.features[0].properties.id : 'N/A');
            }
            
            const routeSectionLayer = L.geoJSON(data, {
                style: function(feature) {
                    // Initial style - will be updated by updateRouteSectionStyling()
                    const status = feature.properties ? feature.properties.status : 'approved';
                    const isPending = status === 'pending';
                    
                    // Lighter/dashed for pending
                    if (isPending) {
                        return {
                            color: '#ff9999',
                            weight: 3,
                            opacity: 0.5,
                            dashArray: '5, 10'
                        };
                    }
                    
                    // Default style (will be updated when selected)
                    return {
                        color: '#0066cc',
                        weight: 3,
                        opacity: 0.7
                    };
                },
                onEachFeature: function(feature, layer) {
                    // GeoJSON ID can be at feature level or in properties
                    const featureId = feature.id !== undefined ? feature.id : (feature.properties ? feature.properties.id : null);
                    const name = (feature.properties && feature.properties.name) || `Section ${featureId}`;
                    const distance = feature.properties ? feature.properties.distance_km : null;
                    const waterbody = feature.properties ? feature.properties.waterbody_name : null;
                    const status = feature.properties ? feature.properties.status : 'approved';
                    const statusText = status === 'pending' ? ' (Pending)' : '';
                    
                    console.log('Route section feature:', {
                        featureId: featureId,
                        featureIdType: typeof featureId,
                        feature: feature,
                        properties: feature.properties
                    });
                    
                    layer.bindTooltip(`${name} - ${distance || 0} km${statusText}`);
                    // Store feature ID on the layer for reference (important for styling updates)
                    layer.featureId = featureId;
                    layer.feature = feature;  // Also store the full feature for reference
                    
                    layer.on('click', function() {
                        if (featureId === null || featureId === undefined) {
                            console.error('Route section feature has no ID:', feature);
                            return;
                        }
                        console.log('Clicking route section with ID:', featureId);
                        // Call the function from route_selection.js directly
                        // Use a small delay to ensure route_selection.js has loaded
                        if (typeof window.toggleRouteSection === 'function') {
                            window.toggleRouteSection(featureId);
                        } else {
                            // Try again after a short delay in case route_selection.js is still loading
                            setTimeout(function() {
                                if (typeof window.toggleRouteSection === 'function') {
                                    window.toggleRouteSection(featureId);
                                } else {
                                    console.error('window.toggleRouteSection is not available. route_selection.js may not be loaded. Make sure route_selection.js is loaded before map.js.');
                                }
                            }, 100);
                        }
                    });
                }
            });
            
            // Add the GeoJSON layer to the layer group
            routeSectionLayer.addTo(layers.routeSections);
            
            // Store reference for easier access
            window.routeSectionLayer = routeSectionLayer;
        })
        .catch(error => console.error('Error loading route sections:', error));

    // Load waypoints
    fetch('/api/waypoints/geojson/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Waypoints loaded:', data);
            if (!data || !data.type || data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
                console.error('Unexpected waypoints data format:', data);
                return;
            }
            if (data.features.length === 0) {
                console.warn('No waypoints found');
                return;
            }
            L.geoJSON(data, {
                pointToLayer: function(feature, latlng) {
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'waypoint-marker',
                            html: '<i class="fa-solid fa-circle" style="color: #666; font-size: 12px;"></i>',
                            iconSize: [12, 12],
                            iconAnchor: [6, 6]
                        })
                    });
                },
                onEachFeature: function(feature, layer) {
                    const name = feature.properties.name || `Waypoint ${feature.properties.id}`;
                    layer.bindTooltip(name);
                }
            }).addTo(layers.waypoints);
        })
        .catch(error => console.error('Error loading waypoints:', error));

    // Load stations
    fetch('/api/stations/geojson/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Stations loaded:', data);
            if (!data || !data.type || data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
                console.error('Unexpected stations data format:', data);
                return;
            }
            if (data.features.length === 0) {
                console.warn('No stations found');
                return;
            }
            L.geoJSON(data, {
                pointToLayer: function(feature, latlng) {
                    const stationTypes = feature.properties.station_types || [];
                    // Use first station type icon
                    const iconClass = stationTypes.length > 0 ? stationTypes[0].icon : 'fa-bus';
                    
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'station-marker',
                            html: `<i class="${iconClass}" style="color: #4a4a4a; font-size: 20px;"></i>`,
                            iconSize: [20, 20],
                            iconAnchor: [10, 10]
                        })
                    });
                },
                onEachFeature: function(feature, layer) {
                    const name = feature.properties.name;
                    layer.bindPopup(`<strong>${name}</strong>`);
                }
            }).addTo(layers.stations);
        })
        .catch(error => console.error('Error loading stations:', error));

    // Load walk paths (optional, can be toggled)
    fetch('/api/walk-paths/geojson/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Walk paths loaded:', data);
            if (!data || !data.type || data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
                console.error('Unexpected walk paths data format:', data);
                return;
            }
            if (data.features.length === 0) {
                console.warn('No walk paths found');
                return;
            }
            L.geoJSON(data, {
                style: {
                    color: '#4a4a4a',
                    dashArray: '1, 6',
                    weight: 3,
                    opacity: 0.9
                },
                onEachFeature: function(feature, layer) {
                    const distance = feature.properties.distance_meters;
                    layer.bindTooltip(`${Math.round(distance)} m`);
                }
            }).addTo(layers.walkPaths);
        })
        .catch(error => console.error('Error loading walk paths:', error));
}

function loadLaunchPointInfo(id) {
    // Load launch point details
    fetch(`/api/launch-point/${id}/`)
        .then(response => response.json())
        .then(data => {
            const infoBox = document.getElementById('info-box');
            if (infoBox) {
                let html = '<div class="info-box-header">';
                html += `<h3>${data.name}</h3>`;
                html += `<span class="status-badge ${data.status}">${data.status_display}</span>`;
                html += `<div style="margin-top: 5px; color: #6c757d; font-size: 0.9rem;">Accessibility: ${data.accessibility_display}</div>`;
                html += '</div>';
                
                if (data.description) {
                    html += `<div class="info-box-description">${data.description}</div>`;
                }
                
                // Display images
                if (data.images && data.images.length > 0) {
                    html += '<div class="info-box-images">';
                    data.images.forEach(img => {
                        const imgUrl = img.image.startsWith('http') ? img.image : `/media/${img.image}`;
                        html += `<img src="${imgUrl}" alt="${img.caption || ''}" loading="lazy">`;
                        if (img.caption) {
                            html += `<div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 10px;">${img.caption}</div>`;
                        }
                    });
                    html += '</div>';
                }
                
                // Display aggregated ratings
                if (data.average_ratings && Object.keys(data.average_ratings).length > 0) {
                    html += '<div class="info-box-ratings">';
                    html += '<h4>Average Ratings</h4>';
                    for (const [category, ratingData] of Object.entries(data.average_ratings)) {
                        html += `<div class="rating-category">`;
                        html += `<span class="category-name">${category.charAt(0).toUpperCase() + category.slice(1)}:</span>`;
                        html += `<span class="rating-value">${ratingData.average.toFixed(1)}</span>`;
                        html += `<span class="rating-count">(${ratingData.count} ${ratingData.count === 1 ? 'rating' : 'ratings'})</span>`;
                        html += `</div>`;
                    }
                    html += '</div>';
                }
                
                // Display comments with ratings
                if (data.comments && data.comments.length > 0) {
                    html += '<div class="info-box-comments">';
                    html += '<h4>Comments</h4>';
                    data.comments.forEach(comment => {
                        const needsFixingClass = comment.needs_fixing ? 'needs-fixing' : '';
                        html += `<div class="comment-item ${needsFixingClass}">`;
                        html += '<div class="comment-header">';
                        html += `<span class="comment-user">${comment.user_username}</span>`;
                        html += `<span class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</span>`;
                        html += '</div>';
                        html += `<div class="comment-text">${comment.text}</div>`;
                        if (comment.needs_fixing) {
                            html += '<span class="needs-fixing-badge">Needs Fixing</span>';
                        }
                        if (comment.ratings && comment.ratings.length > 0) {
                            html += '<div class="comment-ratings">';
                            comment.ratings.forEach(rating => {
                                html += `<span class="comment-rating-item">`;
                                html += `${rating.category_display}: <span class="rating-value">${rating.value}/5</span>`;
                                html += `</span>`;
                            });
                            html += '</div>';
                        }
                        if (comment.images && comment.images.length > 0) {
                            html += '<div class="info-box-images" style="margin-top: 10px;">';
                            comment.images.forEach(img => {
                                const imgUrl = img.image.startsWith('http') ? img.image : `/media/${img.image}`;
                                html += `<img src="${imgUrl}" alt="${img.caption || ''}" loading="lazy">`;
                            });
                            html += '</div>';
                        }
                        html += '</div>';
                    });
                    html += '</div>';
                }
                
                infoBox.innerHTML = html;
                
                // Scroll info box into view
                infoBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        })
        .catch(error => console.error('Error loading launch point info:', error));
}

function loadPOIInfo(id) {
    // Load POI details
    fetch(`/api/poi/${id}/`)
        .then(response => response.json())
        .then(data => {
            const infoBox = document.getElementById('info-box');
            if (infoBox) {
                let html = '<div class="info-box-header">';
                html += `<h3>${data.name}</h3>`;
                html += `<span class="status-badge ${data.status}">${data.status_display}</span>`;
                html += `<div style="margin-top: 5px; color: #6c757d; font-size: 0.9rem;">Type: ${data.poi_type_name} <i class="${data.poi_type_icon}"></i></div>`;
                if (data.accessibility) {
                    html += `<div style="margin-top: 3px; color: #6c757d; font-size: 0.9rem;">Accessibility: ${data.accessibility_display}</div>`;
                }
                html += '</div>';
                
                if (data.description) {
                    html += `<div class="info-box-description">${data.description}</div>`;
                }
                
                // Display images
                if (data.images && data.images.length > 0) {
                    html += '<div class="info-box-images">';
                    data.images.forEach(img => {
                        const imgUrl = img.image.startsWith('http') ? img.image : `/media/${img.image}`;
                        html += `<img src="${imgUrl}" alt="${img.caption || ''}" loading="lazy">`;
                        if (img.caption) {
                            html += `<div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 10px;">${img.caption}</div>`;
                        }
                    });
                    html += '</div>';
                }
                
                // Display comments with ratings
                if (data.comments && data.comments.length > 0) {
                    html += '<div class="info-box-comments">';
                    html += '<h4>Comments</h4>';
                    data.comments.forEach(comment => {
                        const needsFixingClass = comment.needs_fixing ? 'needs-fixing' : '';
                        html += `<div class="comment-item ${needsFixingClass}">`;
                        html += '<div class="comment-header">';
                        html += `<span class="comment-user">${comment.user_username}</span>`;
                        html += `<span class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</span>`;
                        html += '</div>';
                        html += `<div class="comment-text">${comment.text}</div>`;
                        if (comment.needs_fixing) {
                            html += '<span class="needs-fixing-badge">Needs Fixing</span>';
                        }
                        if (comment.ratings && comment.ratings.length > 0) {
                            html += '<div class="comment-ratings">';
                            comment.ratings.forEach(rating => {
                                html += `<span class="comment-rating-item">`;
                                html += `${rating.category_display}: <span class="rating-value">${rating.value}/5</span>`;
                                html += `</span>`;
                            });
                            html += '</div>';
                        }
                        if (comment.images && comment.images.length > 0) {
                            html += '<div class="info-box-images" style="margin-top: 10px;">';
                            comment.images.forEach(img => {
                                const imgUrl = img.image.startsWith('http') ? img.image : `/media/${img.image}`;
                                html += `<img src="${imgUrl}" alt="${img.caption || ''}" loading="lazy">`;
                            });
                            html += '</div>';
                        }
                        html += '</div>';
                    });
                    html += '</div>';
                }
                
                infoBox.innerHTML = html;
                
                // Scroll info box into view
                infoBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        })
        .catch(error => console.error('Error loading POI info:', error));
}

// Route section toggle is handled by route_selection.js
// No local function needed - we call window.toggleRouteSection directly in the click handler
window.map = map;
window.layers = layers;
window.selectedSections = selectedSections;
