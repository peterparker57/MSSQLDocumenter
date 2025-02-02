// Global application state
const appState = {
    connected: false,
    documenting: false,
    searching: false
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Bootstrap tabs
    const documentationTab = document.getElementById('documentation-tab');
    const vectorStoreTab = document.getElementById('vector-store-tab');
    
    if (documentationTab && vectorStoreTab) {
        documentationTab.addEventListener('click', () => {
            showTab('documentation');
        });
        
        vectorStoreTab.addEventListener('click', () => {
            showTab('vector-store');
            // Update vector store stats when tab is shown
            if (window.vectorStoreManager) {
                window.vectorStoreManager.updateStats();
            }
        });
    }

    // Check if we're already connected
    checkConnectionStatus();
});

// Show the specified tab and hide others
function showTab(tabId) {
    const tabs = ['documentation', 'vector-store'];
    tabs.forEach(id => {
        const tab = document.getElementById(id);
        const tabButton = document.getElementById(`${id}-tab`);
        if (tab && tabButton) {
            if (id === tabId) {
                tab.classList.add('show', 'active');
                tabButton.classList.add('active');
            } else {
                tab.classList.remove('show', 'active');
                tabButton.classList.remove('active');
            }
        }
    });
}

// Check connection status on page load
async function checkConnectionStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();

        if (status.connected) {
            appState.connected = true;
            updateUIForConnection();
        }
    } catch (error) {
        console.error('Error checking connection status:', error);
    }
}

// Update UI elements based on connection state
function updateUIForConnection() {
    const connectBtn = document.getElementById('connectBtn');
    const optionsCard = document.getElementById('optionsCard');
    const searchCard = document.getElementById('searchCard');
    const vectorStoreTab = document.getElementById('vector-store-tab');

    if (appState.connected) {
        // Update connect button
        connectBtn.textContent = 'Connected';
        connectBtn.disabled = true;
        connectBtn.classList.remove('btn-primary');
        connectBtn.classList.add('btn-success');

        // Show options and search cards
        optionsCard.style.display = 'block';
        searchCard.style.display = 'block';

        // Enable vector store tab
        if (vectorStoreTab) {
            vectorStoreTab.classList.remove('disabled');
        }

        // Disable connection form fields
        document.getElementById('server').disabled = true;
        document.getElementById('database').disabled = true;
        document.getElementById('trustedConnection').disabled = true;
        document.getElementById('username').disabled = true;
        document.getElementById('password').disabled = true;
    } else {
        // Reset UI to initial state
        connectBtn.textContent = 'Connect';
        connectBtn.disabled = false;
        connectBtn.classList.remove('btn-success');
        connectBtn.classList.add('btn-primary');

        // Hide cards
        optionsCard.style.display = 'none';
        searchCard.style.display = 'none';

        // Disable vector store tab
        if (vectorStoreTab) {
            vectorStoreTab.classList.add('disabled');
        }

        // Enable connection form fields
        document.getElementById('server').disabled = false;
        document.getElementById('database').disabled = false;
        document.getElementById('trustedConnection').disabled = false;
        document.getElementById('username').disabled = false;
        document.getElementById('password').disabled = false;
    }
}

// Handle errors
function handleError(error, context) {
    console.error(`${context}:`, error);
    let errorMessage = error.message;
    
    if (error.response) {
        error.response.json()
            .then(data => {
                errorMessage = data.detail || data.message || errorMessage;
                alert(`${context}: ${errorMessage}`);
            })
            .catch(() => {
                alert(`${context}: ${errorMessage}`);
            });
    } else {
        alert(`${context}: ${errorMessage}`);
    }
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format currency
function formatCurrency(amount) {
    return `$${amount.toFixed(4)}`;
}

// Update progress information
function updateProgress(progress) {
    const progressBar = document.querySelector('.progress-bar');
    const currentObject = document.getElementById('currentObject');
    const processedCount = document.getElementById('processedCount');
    const totalCount = document.getElementById('totalCount');
    const timeRemaining = document.getElementById('timeRemaining');
    const costInfo = document.getElementById('costInfo');
    const tokenInfo = document.getElementById('tokenInfo');

    if (progress.total > 0) {
        const percentage = (progress.current / progress.total * 100).toFixed(1);
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

    if (progress.cost) {
        costInfo.textContent = formatCurrency(progress.cost);
    }

    if (progress.usage && progress.usage.total_tokens) {
        tokenInfo.textContent = formatNumber(progress.usage.total_tokens);
    }
}

// Export functions for use in other modules
window.appState = appState;
window.updateProgress = updateProgress;
window.handleError = handleError;
window.formatNumber = formatNumber;
window.formatCurrency = formatCurrency;