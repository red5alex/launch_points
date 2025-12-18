// HTMX integration and event handlers

document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    htmx.config.useTemplateFragments = true;
    
    // Handle HTMX events
    document.body.addEventListener('htmx:afterSwap', function(event) {
        // Reinitialize any components after HTMX swaps
        console.log('HTMX swap completed:', event.detail.target);
    });
});

