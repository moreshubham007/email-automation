document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('gmailAccountsTable');
    const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    let actionCallback = null;

    // Filter functionality
    document.querySelectorAll('.btn-filter').forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            document.querySelectorAll('.btn-filter').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');

            // Apply filter
            const filter = this.dataset.filter;
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                if (filter === 'all' || row.dataset.status === filter) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // Authentication handling
    document.querySelectorAll('.btn-authenticate').forEach(button => {
        button.addEventListener('click', function() {
            const email = this.dataset.email;
            window.open(`/authenticate/${email}`, 'oauth_window',
                'width=600,height=600,menubar=no,toolbar=no,location=no,status=no');
        });
    });

    // Revoke access
    document.querySelectorAll('.btn-revoke').forEach(button => {
        button.addEventListener('click', function() {
            const email = this.dataset.email;
            showConfirmation(
                `Are you sure you want to revoke access for ${email}?`,
                () => revokeAccess(email)
            );
        });
    });

    // Delete Gmail ID
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function() {
            const email = this.dataset.email;
            showConfirmation(
                `Are you sure you want to delete ${email}?`,
                () => deleteGmailId(email)
            );
        });
    });

    // Confirmation modal helper
    function showConfirmation(message, callback) {
        document.getElementById('confirmationMessage').textContent = message;
        actionCallback = callback;
        confirmationModal.show();
    }

    // Confirm action button
    document.getElementById('confirmAction').addEventListener('click', function() {
        if (actionCallback) {
            actionCallback();
            actionCallback = null;
        }
        confirmationModal.hide();
    });

    // API calls
    async function revokeAccess(email) {
        try {
            const response = await fetch(`/api/gmail/${email}/revoke`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                window.location.reload();
            } else {
                const error = await response.json();
                showError(error.message);
            }
        } catch (error) {
            showError('Failed to revoke access');
        }
    }

    async function deleteGmailId(email) {
        try {
            const response = await fetch(`/api/gmail/${email}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                window.location.reload();
            } else {
                const error = await response.json();
                showError(error.message);
            }
        } catch (error) {
            showError('Failed to delete Gmail ID');
        }
    }

    // Error handling
    function showError(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        table.insertAdjacentHTML('beforebegin', alertHtml);
    }

    // Handle CSV file upload preview
    document.getElementById('csv_file').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const text = e.target.result;
                const rows = text.split('\n').slice(0, 5); // Preview first 5 rows
                const preview = rows.join('\n');
                document.getElementById('csvPreview').textContent = preview;
            };
            reader.readAsText(file);
        }
    });

    // Email validation and form handling
    const singleGmailForm = document.getElementById('singleGmailForm');
    if (singleGmailForm) {
        const emailInput = singleGmailForm.querySelector('input[name="email"]');
        const submitButton = singleGmailForm.querySelector('button[type="submit"]');

        // Real-time email validation
        emailInput.addEventListener('input', function() {
            const email = this.value.trim().toLowerCase();
            
            // Basic email validation
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            const isValidEmail = emailRegex.test(email);
            
            if (isValidEmail) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
                submitButton.disabled = false;
                this.setCustomValidity('');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
                submitButton.disabled = true;
                this.setCustomValidity('Must be a valid email address');
            }
        });

        // Form submission validation
        singleGmailForm.addEventListener('submit', function(e) {
            const email = emailInput.value.trim().toLowerCase();
            const domain = email.split('@')[1];
            
            if (!emailInput.validity.valid) {
                e.preventDefault();
                emailInput.classList.add('is-invalid');
                return false;
            }
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding...';
        });
    }

    // Reset form when modal is closed
    const addSingleGmailModal = document.getElementById('addSingleGmailModal');
    if (addSingleGmailModal) {
        addSingleGmailModal.addEventListener('hidden.bs.modal', function () {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                const inputs = form.querySelectorAll('.form-control');
                inputs.forEach(input => {
                    input.classList.remove('is-valid', 'is-invalid');
                });
                const submitButton = form.querySelector('button[type="submit"]');
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-plus-circle me-1"></i>Add Gmail ID';
            }
        });
    }

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.forEach(function (popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl)
    });

    // Show selected file name
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                const small = this.parentElement.querySelector('small');
                if (small) {
                    small.textContent = `Selected file: ${fileName}`;
                }
            }
        });
    }

    // Form validation feedback
    const projectForm = document.querySelector('form');
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    }
}); 