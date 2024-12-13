document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap modal
    const editModal = new bootstrap.Modal(document.getElementById('editTemplateModal'));

    // Global edit function
    window.editTemplate = function(templateId) {
        fetch(`/api/templates/${templateId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(template => {
                const modalBody = document.querySelector('#editTemplateModal .modal-body');
                modalBody.innerHTML = `
                    <form id="editTemplateForm">
                        <input type="hidden" name="template_id" value="${template.id}">
                        <div class="mb-3">
                            <label class="form-label">Template Name</label>
                            <input type="text" class="form-control" name="name" value="${template.name}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email Subject</label>
                            <input type="text" class="form-control" name="subject" value="${template.subject}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2">${template.description || ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email Body</label>
                            <textarea class="form-control" name="content" rows="10" required>${template.content}</textarea>
                        </div>
                        <div class="d-flex justify-content-end gap-2">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Save Changes</button>
                        </div>
                    </form>
                `;

                // Add form submit handler
                const form = modalBody.querySelector('#editTemplateForm');
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const formData = new FormData(this);
                    const data = {
                        name: formData.get('name'),
                        subject: formData.get('subject'),
                        description: formData.get('description'),
                        content: formData.get('content')
                    };

                    fetch(`/api/templates/${templateId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Failed to update template');
                        }
                        return response.json();
                    })
                    .then(() => {
                        editModal.hide();
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Failed to update template');
                    });
                });

                editModal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load template data');
            });
    };

    // Global delete function
    window.deleteTemplate = function(templateId) {
        if (confirm('Are you sure you want to delete this template?')) {
            fetch(`/api/templates/${templateId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to delete template');
                }
                return response.json();
            })
            .then(() => {
                window.location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete template');
            });
        }
    };

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.forEach(function (popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl)
    });

    const useFileCheckbox = document.getElementById('use_file');
    const fileUploadSection = document.getElementById('fileUploadSection');
    const editorSection = document.getElementById('editorSection');
    const contentTextarea = document.querySelector('textarea[name="content"]');
    const htmlFileInput = document.querySelector('input[name="html_file"]');

    // Toggle between file upload and editor
    useFileCheckbox.addEventListener('change', function() {
        if (this.checked) {
            fileUploadSection.style.display = 'block';
            editorSection.style.display = 'none';
        } else {
            fileUploadSection.style.display = 'none';
            editorSection.style.display = 'block';
        }
    });

    // Handle file selection
    htmlFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                contentTextarea.value = e.target.result;
            };
            reader.readAsText(file);
        }
    });

    // Form validation
    const templateForm = document.getElementById('templateForm');
    templateForm.addEventListener('submit', function(e) {
        if (useFileCheckbox.checked && !htmlFileInput.files[0] && !contentTextarea.value) {
            e.preventDefault();
            alert('Please select an HTML template file to upload');
            return false;
        }
    });

    // Preview functionality
    let previewButton = document.createElement('button');
    previewButton.type = 'button';
    previewButton.className = 'btn btn-outline-secondary me-2';
    previewButton.innerHTML = '<i class="bi bi-eye me-1"></i>Preview';
    previewButton.onclick = function() {
        const content = contentTextarea.value;
        const previewWindow = window.open('', '_blank');
        previewWindow.document.write(content);
        previewWindow.document.close();
    };
    templateForm.querySelector('button[type="submit"]').before(previewButton);
}); 