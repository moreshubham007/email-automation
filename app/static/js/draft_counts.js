document.addEventListener('DOMContentLoaded', function() {
    const projectFilter = document.getElementById('projectFilter');
    const searchInput = document.getElementById('searchInput');
    const fetchAllButton = document.getElementById('fetchAllDrafts');
    const gmailGrid = document.getElementById('gmailGrid');

    // Filter functionality
    function applyFilters() {
        const projectId = projectFilter.value;
        const searchTerm = searchInput.value.toLowerCase();
        
        Array.from(gmailGrid.children).forEach(col => {
            const card = col.querySelector('.card');
            const email = card.querySelector('.card-title').textContent.toLowerCase();
            const cardProjectId = col.dataset.project;
            
            const matchesProject = !projectId || cardProjectId === projectId;
            const matchesSearch = !searchTerm || email.includes(searchTerm);
            
            col.style.display = matchesProject && matchesSearch ? '' : 'none';
        });
    }

    projectFilter.addEventListener('change', applyFilters);
    searchInput.addEventListener('input', applyFilters);

    // Fetch draft count for a single account
    async function fetchDraftCount(accountId) {
        const countElement = document.getElementById(`count-${accountId}`);
        const spinner = document.getElementById(`spinner-${accountId}`);
        const lastUpdate = document.getElementById(`lastUpdate-${accountId}`);
        const button = document.querySelector(`button[data-account-id="${accountId}"]`);

        try {
            button.style.display = 'none';
            spinner.classList.remove('d-none');

            const response = await fetch(`/api/gmail/${accountId}/draft-count`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            countElement.textContent = data.count;
            lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        } catch (error) {
            console.error('Error:', error);
            countElement.textContent = 'Error';
            countElement.classList.add('text-danger');
        } finally {
            spinner.classList.add('d-none');
            button.style.display = 'inline-block';
        }
    }

    // Add click handlers for individual fetch buttons
    document.querySelectorAll('.fetch-drafts').forEach(button => {
        button.addEventListener('click', () => {
            const accountId = button.dataset.accountId;
            fetchDraftCount(accountId);
        });
    });

    // Fetch all draft counts
    fetchAllButton.addEventListener('click', async () => {
        const visibleAccounts = Array.from(gmailGrid.children)
            .filter(col => col.style.display !== 'none')
            .map(col => col.querySelector('.fetch-drafts').dataset.accountId);

        fetchAllButton.disabled = true;
        fetchAllButton.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i>Fetching...';

        for (const accountId of visibleAccounts) {
            await fetchDraftCount(accountId);
        }

        fetchAllButton.disabled = false;
        fetchAllButton.innerHTML = '<i class="bi bi-cloud-download me-1"></i>Fetch All Draft Counts';
    });

    // Add delete draft functionality
    async function deleteDrafts(accountId) {
        const countElement = document.getElementById(`count-${accountId}`);
        const spinner = document.getElementById(`spinner-${accountId}`);
        const lastUpdate = document.getElementById(`lastUpdate-${accountId}`);
        const button = document.querySelector(`button[data-account-id="${accountId}"].delete-drafts`);

        try {
            // Show confirmation dialog
            if (!confirm('Are you sure you want to delete all drafts for this account? This action cannot be undone.')) {
                return;
            }

            button.style.display = 'none';
            spinner.classList.remove('d-none');

            const response = await fetch(`/api/gmail/${accountId}/drafts`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Update count to 0 and show success message
            countElement.textContent = '0';
            lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            showToast('Drafts deleted successfully', 'success');
        } catch (error) {
            console.error('Error:', error);
            showToast('Failed to delete drafts: ' + error.message, 'danger');
        } finally {
            spinner.classList.add('d-none');
            button.style.display = 'inline-block';
        }
    }

    // Add click handlers for delete buttons
    document.querySelectorAll('.delete-drafts').forEach(button => {
        button.addEventListener('click', () => {
            const accountId = button.dataset.accountId;
            deleteDrafts(accountId);
        });
    });

    // Helper function to show toast notifications
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();
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
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Helper function to create toast container if it doesn't exist
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }
}); 