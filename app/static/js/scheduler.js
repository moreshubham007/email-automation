// Add sound functions
function playErrorSound() {
    const errorSound = document.getElementById('errorSound');
    if (errorSound) {
        errorSound.play().catch(function(error) {
            console.log("Error playing sound:", error);
        });
    }
}

function playSuccessSound() {
    const successSound = document.getElementById('successSound');
    if (successSound) {
        successSound.play().catch(function(error) {
            console.log("Error playing sound:", error);
        });
    }
}

// Update the WebSocket message handler
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'log') {
        addLogMessage(data.message, data.level);
        
        // Play sounds based on completion messages
        if (data.message.includes('Completed sending all drafts')) {
            playSuccessSound();
        }
    }
    else if (data.type === 'progress') {
        updateProgress(data.progress);
        
        // Play sound when a sender completes
        if (data.progress.status === 'completed') {
            playSuccessSound();
        }
    }
    else if (data.type === 'error') {
        addLogMessage(data.message, 'danger');
        playErrorSound();
    }
};

// Update error handling
function handleError(error) {
    console.error('Error:', error);
    addLogMessage(error.message || 'An error occurred', 'danger');
    playErrorSound();
} 