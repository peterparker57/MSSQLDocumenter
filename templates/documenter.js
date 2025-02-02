// Handle documentation process
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Bootstrap tabs
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', (e) => {
            const targetId = e.target.getAttribute('data-bs-target');
            if (targetId === '#documentation') {
                // Show documentation cards if connected
                if (window.appState.connected) {
                    document.getElementById('optionsCard').style.display = 'block';
                    document.getElementById('searchCard').style.display = 'block';
                }
            }
        });
    });

    const optionsForm = document.getElementById('optionsForm');
    const progressCard = document.getElementById('progressCard');
    const progressBar = document.querySelector('.progress-bar');
    const currentObject = document.getElementById('currentObject');
    const processedCount = document.getElementById('processedCount');
    const totalCount = document.getElementById('totalCount');
    const timeRemaining = document.getElementById('timeRemaining');
    const costInfo = document.getElementById('costInfo');
    const tokenInfo = document.getElementById('tokenInfo');

    let progressInterval = null;

    optionsForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const startBtn = document.getElementById('startBtn');
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';

        // Reset progress UI
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', '0');
        currentObject.textContent = 'Initializing...';
        processedCount.textContent = '0';
        totalCount.textContent = '0';
        timeRemaining.textContent = 'Calculating...';
        costInfo.textContent = '$0.00';
        tokenInfo.textContent = '0';

        // Show progress card immediately
        progressCard.style.display = 'block';

        // Get selected object types
        const typeMapping = {
            'table': 'tableCheck',
            'view': 'viewCheck',
            'procedure': 'procCheck',
            'function': 'funcCheck'
        };

        const objectTypes = [];
        Object.entries(typeMapping).forEach(([type, id]) => {
            if (document.getElementById(id).checked) {
                objectTypes.push(type);
            }
        });

        const batchRequest = {
            object_types: objectTypes,
            batch_size: parseInt(document.getElementById('batchSize').value),
            include_llm_analysis: document.getElementById('llmCheck').checked
        };

        try {
            console.log('Starting documentation with request:', batchRequest);
            
            const response = await fetch('/api/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(batchRequest)
            });

            console.log('Server response status:', response.status);
            const result = await response.json();
            console.log('Server response:', result);
            
            if (response.ok) {
                console.log('Documentation started successfully');
                startProgressTracking();
            } else {
                console.error('Failed to start documentation:', result);
                alert(`Failed to start documentation: ${result.detail || 'Unknown error'}`);
                startBtn.disabled = false;
                startBtn.textContent = 'Start Documentation';
                progressCard.style.display = 'none';
            }
        } catch (error) {
            console.error('Documentation error:', error);
            alert('Failed to start documentation: ' + error.message);
            startBtn.disabled = false;
            startBtn.textContent = 'Start Documentation';
            progressCard.style.display = 'none';
        }
    });

    function startProgressTracking() {
        if (progressInterval) {
            clearInterval(progressInterval);
        }

        progressInterval = setInterval(async () => {
            try {
                console.log('Checking progress');
                const response = await fetch('/api/batch/progress');
                console.log('Progress response status:', response.status);
                const progress = await response.json();
                console.log('Progress data:', progress);

                // Update progress UI
                if (progress.total > 0) {
                    const percentage = (progress.current / progress.total * 100).toFixed(1);
                    console.log('Progress percentage:', percentage);
                    progressBar.style.width = `${percentage}%`;
                    progressBar.setAttribute('aria-valuenow', percentage);
                }

                currentObject.textContent = progress.current_object || 'Initializing...';
                processedCount.textContent = progress.current;
                totalCount.textContent = progress.total;

                if (progress.estimated_time_remaining !== null) {
                    const minutes = Math.floor(progress.estimated_time_remaining / 60);
                    const seconds = progress.estimated_time_remaining % 60;
                    timeRemaining.textContent = `${minutes}m ${seconds}s`;
                }

                // Update cost and token information
                if (progress.cost !== undefined) {
                    costInfo.textContent = `$${progress.cost.toFixed(4)}`;
                }
                if (progress.usage && progress.usage.total_tokens !== undefined) {
                    tokenInfo.textContent = progress.usage.total_tokens.toLocaleString();
                }

                // Check if complete
                if (progress.phase === 'Complete') {
                    console.log('Documentation completed successfully');
                    clearInterval(progressInterval);
                    showSuccess('Documentation completed successfully!');
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('startBtn').textContent = 'Start Documentation';
                    // Update vector store stats
                    if (window.vectorStoreManager) {
                        window.vectorStoreManager.updateStats();
                    }
                } else if (progress.phase === 'Failed') {
                    console.error('Documentation failed:', progress.error);
                    clearInterval(progressInterval);
                    showError('documentationError', 'Documentation failed: ' + (progress.error || 'Unknown error'));
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('startBtn').textContent = 'Start Documentation';
                }
            } catch (error) {
                console.error('Progress tracking error:', error);
                // Don't clear the interval on error - keep trying
            }
        }, 1000);
    }
});