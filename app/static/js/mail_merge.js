document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('mailMergeForm');
    const csvInput = document.getElementById('csvFile');
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
                    
                    // Validate required headers
                    const requiredHeaders = ['template_name', 'sender_email', 'email'];
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

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!csvData) {
            alert('Please select a CSV file first');
            return;
        }

        const formData = new FormData();
        formData.append('csv_data', JSON.stringify(csvData));
        formData.append('test_mode', form.test_mode.checked);

        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Processing...';

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
            } else {
                alert(`Successfully created ${data.results.success.length} drafts`);
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error: ' + error.message);
        })
        .finally(() => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        });
    });
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
                <strong>From:</strong> ${preview.sender_email}<br>
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