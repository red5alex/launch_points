// Route selection logic
let searchRadius = 500; // meters

function toggleRouteSection(sectionId) {
    console.log('toggleRouteSection called with ID:', sectionId);
    // Use the global selectedSections from map.js
    if (!window.selectedSections) {
        window.selectedSections = new Set();
    }
    if (window.selectedSections.has(sectionId)) {
        window.selectedSections.delete(sectionId);
        console.log('Removed section', sectionId, 'from selection. Total:', window.selectedSections.size);
    } else {
        window.selectedSections.add(sectionId);
        console.log('Added section', sectionId, 'to selection. Total:', window.selectedSections.size);
    }
    updateRouteDisplay();
    // Update map layer styling
    updateRouteSectionStyling();
}

function updateRouteSectionStyling() {
    // Update the visual styling of route sections based on selection
    if (!window.layers || !window.layers.routeSections) {
        console.warn('Route sections layer not available for styling update');
        return;
    }
    
    if (!window.selectedSections) {
        window.selectedSections = new Set();
    }
    
    let updatedCount = 0;
    let checkedCount = 0;
    let missingIdCount = 0;
    
    console.log(`Starting styling update. Selected sections: [${Array.from(window.selectedSections).join(', ')}]`);
    
    // L.geoJSON creates a FeatureGroup, which when added to layers.routeSections creates nested groups
    // We need to iterate through the FeatureGroup's layers, not the outer LayerGroup
    const allLayers = window.layers.routeSections.getLayers();
    console.log(`Route sections layer group has ${allLayers.length} top-level layers`);
    
    // Iterate through all layers - handle both direct layers and nested FeatureGroups
    window.layers.routeSections.eachLayer(function(layer) {
        // Check if this is a FeatureGroup (from L.geoJSON)
        if (layer instanceof L.FeatureGroup || layer instanceof L.GeoJSON) {
            // Iterate through the FeatureGroup's layers
            layer.eachLayer(function(featureLayer) {
                checkedCount++;
                updateLayerStyle(featureLayer, checkedCount);
            });
        } else {
            // Direct layer
            checkedCount++;
            updateLayerStyle(layer, checkedCount);
        }
    });
    
    function updateLayerStyle(layer, layerIndex) {
        // Get ID from layer.featureId (set in map.js) or from feature
        let sectionId = layer.featureId;
        
        // If featureId not set, try to get it from the feature
        if (sectionId === undefined || sectionId === null) {
            if (layer.feature) {
                sectionId = layer.feature.id !== undefined ? layer.feature.id : (layer.feature.properties ? layer.feature.properties.id : null);
            }
        }
        
        // Debug first few layers or if we're looking for a specific ID
        if (layerIndex <= 5 || sectionId === 15) {
            console.log(`Layer ${layerIndex}: featureId=${layer.featureId}, sectionId=${sectionId}, has feature=${!!layer.feature}, feature.id=${layer.feature ? layer.feature.id : 'N/A'}, layer type=${layer.constructor.name}`);
        }
        
        if (sectionId === null || sectionId === undefined) {
            missingIdCount++;
            // Skip layers without IDs (shouldn't happen, but be defensive)
            return;
        }
        
        // Convert to number for comparison (in case it's a string)
        const sectionIdNum = typeof sectionId === 'string' ? parseInt(sectionId, 10) : sectionId;
        
        // Check if this section is selected (check both number and original value)
        const isSelected = window.selectedSections.has(sectionIdNum) || 
                          window.selectedSections.has(sectionId) ||
                          (typeof sectionId === 'number' && window.selectedSections.has(String(sectionId)));
        
        const isPending = layer.feature && layer.feature.properties && layer.feature.properties.status === 'pending';
        
        // Debug selected sections
        if (isSelected || sectionId === 15) {
            console.log(`Section ${sectionId} (num: ${sectionIdNum}): isSelected=${isSelected}, selectedSections=[${Array.from(window.selectedSections).join(', ')}]`);
        }
        
        // Apply styling based on selection and status
        if (isSelected) {
            layer.setStyle({
                color: '#ff0000',  // Red for selected
                weight: 5,         // Thicker line
                opacity: 0.9,      // More opaque
                dashArray: null    // Solid line
            });
            updatedCount++;
            console.log(`✓ Highlighted section ${sectionId} in red`);
        } else if (isPending) {
            layer.setStyle({
                color: '#ff9999',  // Light red for pending
                weight: 3,
                opacity: 0.5,
                dashArray: '5, 10' // Dashed line
            });
        } else {
            layer.setStyle({
                color: '#0066cc',  // Blue for normal
                weight: 3,
                opacity: 0.7,
                dashArray: null    // Solid line
            });
        }
    }
    
    console.log(`Updated styling: Checked ${checkedCount} layers, ${missingIdCount} missing IDs, ${updatedCount} selected sections highlighted`);
    console.log(`Selected sections: [${Array.from(window.selectedSections).join(', ')}]`);
}

function updateRouteDisplay() {
    if (!window.selectedSections || window.selectedSections.size === 0) {
        const routeList = document.getElementById('route-list');
        if (routeList) {
            routeList.innerHTML = '';
        }
        return;
    }

    // Convert Set to array and ensure IDs are numbers
    const sectionIds = Array.from(window.selectedSections).map(id => {
        const numId = typeof id === 'string' ? parseInt(id, 10) : id;
        if (isNaN(numId)) {
            console.error('Invalid section ID:', id);
            return null;
        }
        return numId;
    }).filter(id => id !== null);
    
    console.log('Calculating route with sections:', sectionIds, 'radius:', searchRadius);
    console.log('selectedSections Set:', window.selectedSections);
    console.log('sectionIds array (converted):', sectionIds);
    console.log('sectionIds type:', typeof sectionIds, 'isArray:', Array.isArray(sectionIds));
    
    if (sectionIds.length === 0) {
        console.warn('No valid sections selected');
        const routeList = document.getElementById('route-list');
        if (routeList) {
            routeList.innerHTML = '<div style="color: orange; padding: 10px;">No sections selected. Click on route sections on the map to select them.</div>';
        }
        return;
    }
    
    let csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('CSRF token not found in cookies');
        // Try to get it from meta tag if available
        const metaToken = document.querySelector('meta[name=csrf-token]');
        if (metaToken) {
            csrfToken = metaToken.getAttribute('content');
            console.log('Got CSRF token from meta tag');
        } else {
            console.error('CSRF token not found in meta tag either');
        }
    } else {
        console.log('Got CSRF token from cookie');
    }

    const requestBody = {
        section_ids: sectionIds,
        search_radius_meters: searchRadius
    };
    console.log('Request body:', JSON.stringify(requestBody));

    fetch('/api/calculate-route/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        },
        credentials: 'same-origin',
        body: JSON.stringify(requestBody)
    })
    .then(async response => {
        console.log('Response status:', response.status, response.statusText);
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!response.ok) {
            console.error('API error response:', data);
            const errorMsg = data.error || data.message || JSON.stringify(data);
            throw new Error(`HTTP ${response.status}: ${errorMsg}`);
        }
        return data;
    })
    .then(data => {
        console.log('Route calculation response:', data);
        console.log('Response keys:', Object.keys(data || {}));
        // Check if response is an error
        if (data.error) {
            throw new Error(data.error);
        }
        // Validate response structure
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid response format: ' + JSON.stringify(data));
        }
        // Check if sections exist
        if (!data.sections) {
            console.warn('Response missing sections property. Full response:', data);
            throw new Error('Response missing sections property. Received: ' + JSON.stringify(data));
        }
        displayRouteInfo(data);
    })
    .catch(error => {
        console.error('Error calculating route:', error);
        const routeList = document.getElementById('route-list');
        if (routeList) {
            routeList.innerHTML = `<div style="color: red; padding: 10px;">Error: ${error.message}</div>`;
        }
    });
}

function displayRouteInfo(data) {
    const routeList = document.getElementById('route-list');
    if (!routeList) {
        console.error('Route list element not found');
        return;
    }
    
    // Validate data structure
    if (!data || typeof data !== 'object') {
        routeList.innerHTML = '<div style="color: red; padding: 10px;">Invalid response data</div>';
        return;
    }
    
    let html = '';
    
    // Display route sections
    if (data.sections && Array.isArray(data.sections) && data.sections.length > 0) {
        html += '<div class="route-sections">';
        data.sections.forEach(section => {
            html += `<div class="route-section-item">
                <div>
                    <strong>${section.name || 'Section ' + section.id}</strong>
                    ${section.from_waypoint ? `<br><small>From: ${section.from_waypoint}</small>` : ''}
                    ${section.to_waypoint ? `<br><small>To: ${section.to_waypoint}</small>` : ''}
                </div>
                <span>${section.distance_km.toFixed(2)} km</span>
            </div>`;
        });
        html += '</div>';
        if (data.total_distance_km !== undefined) {
            html += `<div class="route-total">Total Distance: ${data.total_distance_km.toFixed(2)} km</div>`;
        }
    } else {
        html += '<div style="padding: 10px; color: #6c757d;">No route sections selected</div>';
    }
    
    // Display waypoints
    if (data.waypoints && Array.isArray(data.waypoints) && data.waypoints.length > 0) {
        html += '<div class="waypoints-section" style="margin-top: 15px;">';
        html += '<h4>Waypoints</h4>';
        html += '<ul style="list-style: none; padding: 0;">';
        data.waypoints.forEach(waypoint => {
            html += `<li style="padding: 5px 0;">• ${waypoint.name || 'Waypoint ' + waypoint.id}</li>`;
        });
        html += '</ul>';
        html += '</div>';
    }
    
    // Display nearby launch points
    if (data.nearby_launch_points && Array.isArray(data.nearby_launch_points) && data.nearby_launch_points.length > 0) {
        html += '<div class="nearby-points">';
        html += '<h4>Nearby Launch Points</h4>';
        html += '<ul>';
        data.nearby_launch_points.forEach(point => {
            const distanceKm = (point.distance_meters / 1000).toFixed(2);
            html += `<li onclick="loadLaunchPointInfo(${point.id})" style="cursor: pointer;">
                ${point.name}
                <span class="distance">${distanceKm} km</span>
            </li>`;
        });
        html += '</ul>';
        html += '</div>';
    }
    
    // Display nearby POIs
    if (data.nearby_pois && Array.isArray(data.nearby_pois) && data.nearby_pois.length > 0) {
        html += '<div class="nearby-points">';
        html += '<h4>Nearby Points of Interest</h4>';
        html += '<ul>';
        data.nearby_pois.forEach(poi => {
            const distanceKm = (poi.distance_meters / 1000).toFixed(2);
            html += `<li onclick="loadPOIInfo(${poi.id})" style="cursor: pointer;">
                ${poi.name} <small>(${poi.poi_type})</small>
                <span class="distance">${distanceKm} km</span>
            </li>`;
        });
        html += '</ul>';
        html += '</div>';
    }
    
    routeList.innerHTML = html;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    // Fallback: try to get from meta tag
    if (!cookieValue) {
        const metaToken = document.querySelector('meta[name=csrf-token]');
        if (metaToken) {
            cookieValue = metaToken.getAttribute('content');
        }
    }
    return cookieValue;
}

// Search radius widget
document.addEventListener('DOMContentLoaded', function() {
    const radiusInput = document.getElementById('search-radius');
    if (radiusInput) {
        radiusInput.addEventListener('input', function(e) {
            searchRadius = parseInt(e.target.value);
            const display = document.getElementById('radius-display');
            if (display) {
                display.textContent = searchRadius + ' m';
            }
            if (window.selectedSections && window.selectedSections.size > 0) {
                updateRouteDisplay();
            }
        });
    }
});

// Export function for use in map.js
// Make sure it's available globally
window.toggleRouteSection = toggleRouteSection;
window.updateRouteDisplay = updateRouteDisplay;
window.updateRouteSectionStyling = updateRouteSectionStyling;

// Initialize selectedSections if not already set
if (!window.selectedSections) {
    window.selectedSections = new Set();
}

console.log('route_selection.js loaded. toggleRouteSection exported to window.');

