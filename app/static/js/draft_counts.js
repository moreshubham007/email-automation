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
}); 