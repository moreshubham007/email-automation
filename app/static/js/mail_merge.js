document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('mailMergeForm');
    const csvInput = document.getElementById('csvFile');
    const startBtn = document.getElementById('startMergeBtn');
    const resumeBtn = document.getElementById('resumeMergeBtn');
    const stopBtn = document.getElementById('stopMergeBtn');
    const pauseBtn = document.getElementById('pauseMergeBtn');
    const progressSection = document.getElementById('progressSection');
    let mergeInProgress = false;
    let mergePaused = false;
    let csvData = null;

    csvInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    // Parse CSV
                    const csv = e.target.result;
                    const lines = csv.split('\n');
                    const headers = lines[0].split(',').map(h => h.trim());
                    
                    // Update required headers
                    const requiredHeaders = ['template_name', 'sender_email', 'sender_name', 'email'];
                    const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
                    
                    if (missingHeaders.length > 0) {
                        throw new Error(`Missing required headers: ${missingHeaders.join(', ')}`);
                    }
                    
                    // Parse records
                    csvData = lines.slice(1)
                        .filter(line => line.trim())
                        .map(line => {
                            const values = line.split(',').map(v => v.trim());
                            return headers.reduce((obj, header, i) => {
                                obj[header] = values[i];
                                return obj;
                            }, {});
                        });
                        
                    console.log('CSV data loaded:', csvData);
                } catch (error) {
                    console.error('Error parsing CSV:', error);
                    alert('Error parsing CSV: ' + error.message);
                    csvInput.value = '';
                    csvData = null;
                }
            };
            reader.readAsText(file);
        }
    });

    // WebSocket connection for real-time updates
    function setupWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
        
        ws.onopen = function() {
            console.log('WebSocket connected');
            // Start ping interval when connected
            startPing(ws);
        };
        
        ws.onclose = function() {
            console.log('WebSocket disconnected, attempting to reconnect...');
            setTimeout(setupWebSocket, 3000); // Try to reconnect after 3 seconds
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        ws.onmessage = function(event) {
            if (event.data === 'pong') {
                // Handle pong response
                ws.isAlive = true;
                return;
            }
            const data = JSON.parse(event.data);
            updateProgress(data);
        };
        
        return ws;
    }

    function startPing(ws) {
        ws.isAlive = true;
        const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                if (!ws.isAlive) {
                    clearInterval(pingInterval);
                    ws.close();
                    return;
                }
                ws.isAlive = false;
                ws.send('ping');
            } else {
                clearInterval(pingInterval);
            }
        }, 30000); // Send ping every 30 seconds
        
        // Clear interval when websocket closes
        ws.addEventListener('close', () => clearInterval(pingInterval));
    }

    // Initialize WebSocket connection
    let ws = setupWebSocket();

    // Health check interval
    setInterval(() => {
        if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
            console.log('WebSocket connection lost, attempting to reconnect...');
            ws = setupWebSocket();
        }
    }, 5000);

    function updateButtonStates(status) {
        startBtn.classList.add('d-none');
        pauseBtn.classList.add('d-none');
        resumeBtn.classList.add('d-none');
        stopBtn.classList.add('d-none');

        switch(status) {
            case 'running':
                pauseBtn.classList.remove('d-none');
                stopBtn.classList.remove('d-none');
                break;
            case 'paused':
                resumeBtn.classList.remove('d-none');
                stopBtn.classList.remove('d-none');
                break;
            case 'stopped':
            case 'completed':
                startBtn.classList.remove('d-none');
                break;
        }

        // Update status text
        const statusElement = document.getElementById('mergeStatus');
        if (statusElement) {
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
    }

    function updateProgress(data) {
        if (!progressSection.classList.contains('d-none')) {
            try {
                const progress = document.getElementById('mergeProgress');
                const status = document.getElementById('mergeStatus');
                const processed = document.getElementById('processedCount');
                const total = document.getElementById('totalCount');
                const success = document.getElementById('successCount');
                const failed = document.getElementById('failedCount');
                const current = document.getElementById('currentOperation');
                const logContainer = document.getElementById('logContainer');

                if (data.type === 'progress') {
                    const percentage = (data.processed / data.total) * 100;
                    progress.style.width = `${percentage}%`;
                    progress.setAttribute('aria-valuenow', percentage);
                    
                    status.textContent = data.status;
                    processed.textContent = data.processed;
                    total.textContent = data.total;
                    success.textContent = data.success;
                    failed.textContent = data.failed;
                    current.textContent = data.currentOperation;

                    updateButtonStates(data.status);

                    // Only show pause reason modal when status changes to paused
                    if (data.status === 'paused' && data.pauseReason && data.showPauseReason) {
                        showPauseReason(data.pauseReason);
                    }
                } else if (data.type === 'log') {
                    const logEntry = document.createElement('div');
                    logEntry.className = `log-entry text-${data.level}`;
                    logEntry.textContent = `${new Date().toLocaleTimeString()}: ${data.message}`;
                    logContainer.insertBefore(logEntry, logContainer.firstChild);
                }
            } catch (error) {
                console.error('Error updating progress:', error);
                // Attempt to reconnect WebSocket if there's an issue
                ws = setupWebSocket();
            }
        }
    }

    function showPauseReason(reason) {
        const modal = document.getElementById('pauseReasonModal');
        const reasonText = document.getElementById('pauseReason');
        reasonText.textContent = reason;
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!csvData) {
            alert('Please select a CSV file first');
            return;
        }

        const formData = new FormData();
        formData.append('csv_data', JSON.stringify(csvData));
        formData.append('test_mode', form.test_mode.checked);

        updateButtonStates('running');
        progressSection.classList.remove('d-none');
        mergeInProgress = true;
        mergePaused = false;

        fetch('/api/mail-merge', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            if (data.preview) {
                showPreview(data.preview);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addLog('error', 'Error: ' + error.message);
        });
    });

    pauseBtn.addEventListener('click', function() {
        if (!confirm('Are you sure you want to pause the mail merge process?')) {
            return;
        }
        
        fetch('/api/mail-merge/pause', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            updateButtonStates('paused');
            addLog('info', 'Mail merge paused by user');
        })
        .catch(error => {
            console.error('Error pausing merge:', error);
            addLog('error', 'Error pausing merge: ' + error.message);
        });
    });

    resumeBtn.addEventListener('click', function() {
        fetch('/api/mail-merge/resume', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            updateButtonStates('running');
            addLog('info', 'Mail merge resumed');
        })
        .catch(error => {
            console.error('Error resuming merge:', error);
            addLog('error', 'Error resuming merge: ' + error.message);
        });
    });

    stopBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to stop the mail merge process?')) {
            fetch('/api/mail-merge/stop', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                addLog('warning', 'Mail merge operation stopped by user');
                mergeInProgress = false;
                mergePaused = false;
                updateButtonStates('stopped');
            })
            .catch(error => {
                console.error('Error stopping merge:', error);
                addLog('error', 'Error stopping merge: ' + error.message);
            });
        }
    });

    function addLog(level, message) {
        const logContainer = document.getElementById('logContainer');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry text-${level}`;
        logEntry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
        logContainer.insertBefore(logEntry, logContainer.firstChild);
    }
});

function showPreview(previews) {
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');
    container.innerHTML = '';

    previews.forEach(preview => {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'preview-item mb-4 p-3 border rounded';
        previewDiv.innerHTML = `
            <div class="mb-2">
                <strong>Template:</strong> ${preview.template_name}<br>
                <strong>From:</strong> ${preview.sender || preview.sender_email}<br>
                <strong>To:</strong> ${preview.recipient}<br>
                <strong>Subject:</strong> ${preview.subject}
            </div>
            <div class="preview-content border p-2 bg-light">
                ${preview.content}
            </div>
        `;
        container.appendChild(previewDiv);
    });

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
} 