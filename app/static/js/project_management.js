document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap modals
    const editModal = new bootstrap.Modal(document.getElementById('editProjectModal'));
    const viewModal = new bootstrap.Modal(document.getElementById('viewProjectModal'));

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.forEach(function (popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl)
    });

    // Global edit function
    window.editProject = function(projectId) {
        fetch(`/api/projects/${projectId}`)
            .then(response => response.json())
            .then(project => {
                const modalBody = document.querySelector('#editProjectModal .modal-body');
                modalBody.innerHTML = `
                    <form id="editProjectForm">
                        <input type="hidden" name="project_id" value="${project.id}">
                        <div class="mb-3">
                            <label class="form-label">Project Name</label>
                            <input type="text" class="form-control" name="name" value="${project.name}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2">${project.description || ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Client Secret File</label>
                            <input type="file" class="form-control" name="client_secret" accept=".json">
                            <small class="text-muted">Leave empty to keep current file</small>
                        </div>
                        <div class="d-flex justify-content-end gap-2">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Save Changes</button>
                        </div>
                    </form>
                `;

                const form = modalBody.querySelector('#editProjectForm');
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const formData = new FormData(this);

                    fetch(`/api/projects/${projectId}`, {
                        method: 'PUT',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(() => {
                        editModal.hide();
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Failed to update project');
                    });
                });

                editModal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load project data');
            });
    };

    // Global view function
    window.viewProject = function(projectId) {
        fetch(`/api/projects/${projectId}/details`)
            .then(response => response.json())
            .then(project => {
                const modalBody = document.querySelector('#viewProjectModal .modal-body');
                modalBody.innerHTML = `
                    <div class="project-details">
                        <h6>Project Information</h6>
                        <dl class="row mb-4">
                            <dt class="col-sm-3">Name</dt>
                            <dd class="col-sm-9">${project.name}</dd>
                            
                            <dt class="col-sm-3">Description</dt>
                            <dd class="col-sm-9">${project.description || '-'}</dd>
                            
                            <dt class="col-sm-3">Created</dt>
                            <dd class="col-sm-9">${new Date(project.created_at).toLocaleDateString()}</dd>
                        </dl>

                        <h6>Gmail Accounts</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Email</th>
                                        <th>Status</th>
                                        <th>Added</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${project.gmail_accounts.map(account => `
                                        <tr>
                                            <td>${account.email}</td>
                                            <td>
                                                <span class="badge ${account.authenticated ? 'bg-success' : 'bg-warning'}">
                                                    ${account.authenticated ? 'Authenticated' : 'Not Authenticated'}
                                                </span>
                                            </td>
                                            <td>${new Date(account.created_at).toLocaleDateString()}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;

                viewModal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load project details');
            });
    };

    // Global delete function
    window.deleteProject = function(projectId) {
        if (confirm('Are you sure you want to delete this project? This will also remove all associated Gmail accounts.')) {
            fetch(`/api/projects/${projectId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(() => {
                window.location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete project');
            });
        }
    };
}); 