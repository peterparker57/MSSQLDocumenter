document.addEventListener('DOMContentLoaded', () => {
    const connectionForm = document.getElementById('connectionForm');
    const trustedConnection = document.getElementById('trustedConnection');
    const sqlAuthFields = document.getElementById('sqlAuthFields');
    const connectBtn = document.getElementById('connectBtn');
    const optionsCard = document.getElementById('optionsCard');
    const searchCard = document.getElementById('searchCard');
    const vectorStoreTab = document.getElementById('vector-store-tab');

    // Initialize vector store manager
    window.vectorStoreManager = new VectorStoreManager();

    // Toggle SQL authentication fields
    trustedConnection.addEventListener('change', () => {
        sqlAuthFields.style.display = trustedConnection.checked ? 'none' : 'block';
    });

    // Handle connection form submission
    connectionForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const server = document.getElementById('server').value;
        const database = document.getElementById('database').value;
        const useWindowsAuth = trustedConnection.checked;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting...';

        try {
            const connectionData = {
                server,
                database,
                trusted_connection: useWindowsAuth
            };

            if (!useWindowsAuth) {
                connectionData.username = username;
                connectionData.password = password;
            }

            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(connectionData)
            });

            const result = await response.json();

            if (response.ok) {
                console.log('Connection successful:', result);
                // Update global state
                window.appState.connected = true;
                // Show options and search cards
                optionsCard.style.display = 'block';
                searchCard.style.display = 'block';
                // Update connect button
                connectBtn.textContent = 'Connected';
                connectBtn.classList.remove('btn-primary');
                connectBtn.classList.add('btn-success');
                // Enable vector store tab
                if (vectorStoreTab) {
                    vectorStoreTab.classList.remove('disabled');
                    // Update vector store stats
                    window.vectorStoreManager.updateStats();
                }
                // Disable form fields
                document.getElementById('server').disabled = true;
                document.getElementById('database').disabled = true;
                document.getElementById('trustedConnection').disabled = true;
                document.getElementById('username').disabled = true;
                document.getElementById('password').disabled = true;
            } else {
                console.error('Connection failed:', result);
                showError('connectionError', `Connection failed: ${result.detail || 'Unknown error'}`);
                connectBtn.disabled = false;
                connectBtn.textContent = 'Connect';
            }
        } catch (error) {
            console.error('Connection error:', error);
            showError('connectionError', 'Connection failed: ' + error.message);
            connectBtn.disabled = false;
            connectBtn.textContent = 'Connect';
        }
    });

    // Handle search form submission
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const query = document.getElementById('searchQuery').value;
        const searchBtn = searchForm.querySelector('button[type="submit"]');
        searchBtn.disabled = true;
        searchBtn.textContent = 'Searching...';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            const results = await response.json();

            if (response.ok) {
                // Clear previous results
                searchResults.innerHTML = '';

                if (results.length === 0) {
                    searchResults.innerHTML = '<p class="text-muted">No results found.</p>';
                } else {
                    // Create results HTML
                    const resultsHtml = results.map(result => `
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">${result.metadata.type}: ${result.metadata.schema}.${result.metadata.name}</h5>
                                <p class="card-text">${result.content}</p>
                            </div>
                        </div>
                    `).join('');

                    searchResults.innerHTML = resultsHtml;
                }
            } else {
                console.error('Search failed:', results);
                showError('searchError', `Search failed: ${results.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Search error:', error);
            showError('searchError', 'Search failed: ' + error.message);
        } finally {
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search';
        }
    });
});