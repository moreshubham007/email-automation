document.addEventListener('DOMContentLoaded', function() {
    // Initialize status tracking
    let statusSource = null;
    let updateTimer = null;
    
    // Connect to status stream
    function connectStatusStream() {
        statusSource = new EventSource('/api/status/stream');
        
        statusSource.onmessage = function(event) {
            if (event.data === '{}') return; // ignore keepalive
            
            const update = JSON.parse(event.data);
            handleStatusUpdate(update);
        };
        
        statusSource.onerror = function() {
            statusSource.close();
            // Attempt to reconnect after 5 seconds
            setTimeout(connectStatusStream, 5000);
        };
    }
    
    // Handle status updates
    function handleStatusUpdate(update) {
        switch(update.type) {
            case 'mail_merge_start':
                showToast('Mail merge started', 'info');
                updateStats();
                break;
                
            case 'mail_merge_complete':
                showToast(
                    update.success ? 'Mail merge completed successfully' : 'Mail merge completed with errors',
                    update.success ? 'success' : 'warning'
                );
                updateStats();
                break;
                
            case 'mail_merge_error':
                showToast('Mail merge error: ' + update.error, 'danger');
                updateStats();
                break;
                
            case 'authentication_start':
                showToast('Authentication started for ' + update.email, 'info');
                updateStats();
                break;
                
            case 'authentication_complete':
                showToast(
                    'Authentication ' + (update.success ? 'successful' : 'failed') + ' for ' + update.email,
                    update.success ? 'success' : 'danger'
                );
                updateStats();
                break;
        }
    }
    
    // Update dashboard stats
    function updateStats() {
        fetch('/api/status')
            .then(response => response.json())
            .then(stats => {
                // Update Gmail accounts card
                document.getElementById('gmailCount').textContent = 
                    `${stats.authenticated_senders} / ${stats.total_senders}`;
                
                // Update templates card
                document.getElementById('templateCount').textContent = 
                    stats.total_templates;
                
                // Update projects card
                document.getElementById('projectCount').textContent = 
                    stats.active_projects;
                
                // Update ongoing processes
                if (stats.ongoing_merges > 0 || stats.authenticating > 0) {
                    document.getElementById('ongoingProcesses').style.display = 'block';
                    document.getElementById('mergeCount').textContent = stats.ongoing_merges;
                    document.getElementById('authCount').textContent = stats.authenticating;
                } else {
                    document.getElementById('ongoingProcesses').style.display = 'none';
                }
            })
            .catch(error => console.error('Failed to update stats:', error));
    }
    
    // Show toast notification
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.getElementById('toastContainer').appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }
    
    // Start status updates
    connectStatusStream();
    updateStats();
    
    // Update stats periodically
    updateTimer = setInterval(updateStats, 30000);
}); 