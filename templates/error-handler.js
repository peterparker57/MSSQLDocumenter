// Error handling and progress tracking utilities
function showError(elementId, message, type = 'error') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        const icon = type === 'error' ? '⚠️' : 'i️';
        errorElement.innerHTML = `
            <div class="alert ${type === 'error' ? 'alert-danger' : 'alert-warning'} d-flex align-items-center">
                <span class="me-2">${icon}</span>
                <div class="flex-grow-1">${formatErrorMessage(message)}</div>
                <button type="button" class="btn-close" onclick="hideError('${elementId}')"></button>
            </div>
        `;
        errorElement.style.display = 'block';
        
        // Scroll error into view if not visible
        const rect = errorElement.getBoundingClientRect();
        const isVisible = (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
        
        if (!isVisible) {
            errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        // Auto-hide after 10 seconds for warnings
        if (type !== 'error') {
            setTimeout(() => hideError(elementId), 10000);
        }
    }
}

function showSuccess(message, duration = 5000) {
    // Create a success message element if it doesn't exist
    let successElement = document.getElementById('successMessage');
    if (!successElement) {
        successElement = document.createElement('div');
        successElement.id = 'successMessage';
        successElement.style.position = 'fixed';
        successElement.style.top = '20px';
        successElement.style.right = '20px';
        successElement.style.zIndex = '1050';
        document.body.appendChild(successElement);
    }

    // Show the success message
    successElement.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <span class="me-2">✓</span>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    // Auto-hide after duration
    setTimeout(() => {
        const alert = successElement.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');
            setTimeout(() => {
                if (successElement.parentNode) {
                    successElement.parentNode.removeChild(successElement);
                }
            }, 150);
        }
    }, duration);
}

function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.innerHTML = '';
    }
}

function formatErrorMessage(message) {
    // Check if message is a stack trace or technical error
    if (message.includes('\n') || message.includes('  at ')) {
        return `
            <div class="mb-2">${message.split('\n')[0]}</div>
            <button class="btn btn-sm btn-outline-danger" 
                    onclick="toggleDetails(this)">
                Show Details
            </button>
            <pre class="error-details mt-2" style="display: none;">${message}</pre>
        `;
    }
    return message;
}

function toggleDetails(button) {
    const details = button.nextElementSibling;
    const isHidden = details.style.display === 'none';
    details.style.display = isHidden ? 'block' : 'none';
    button.textContent = isHidden ? 'Hide Details' : 'Show Details';
}

// Progress tracking
function showProgress(elementId) {
    const progressElement = document.getElementById(elementId);
    if (progressElement) {
        progressElement.style.display = 'block';
        progressElement.innerHTML = `
            <div class="progress-indicator">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

function hideProgress(elementId) {
    const progressElement = document.getElementById(elementId);
    if (progressElement) {
        progressElement.style.display = 'none';
        progressElement.innerHTML = '';
    }
}

function updateProgress(elementId, progress) {
    const progressBar = document.querySelector(`#${elementId} .progress-bar`);
    if (progressBar) {
        const percentage = Math.round(progress * 100);
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${percentage}%`;
        
        // Update progress bar color based on percentage
        if (percentage < 30) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (percentage < 70) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    }
}

// Helper function to handle API responses
async function handleApiResponse(response, errorElementId) {
    hideError(errorElementId); // Clear any existing errors

    if (!response.ok) {
        let errorMessage;
        try {
            const data = await response.json();
            errorMessage = formatApiError(data, response.status);
        } catch {
            errorMessage = `Server Error: ${response.status} ${response.statusText}`;
        }
        showError(errorElementId, errorMessage);
        return null;
    }
    
    try {
        const data = await response.json();
        if (data.status === 'success') {
            return data;
        } else {
            const errorMessage = formatApiError(data);
            showError(errorElementId, errorMessage);
            return null;
        }
    } catch (error) {
        showError(errorElementId, 'Failed to parse server response: ' + error.message);
        return null;
    }
}

function formatApiError(data, status = null) {
    // Handle various error response formats
    const errorDetail = data.detail || data.message || data.error;
    
    if (typeof errorDetail === 'object') {
        // Handle nested error objects
        return Object.entries(errorDetail)
            .map(([key, value]) => `${key}: ${value}`)
            .join('\n');
    }

    if (status) {
        const statusMessages = {
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        };
        
        const statusText = statusMessages[status] || `Error ${status}`;
        return `${statusText}: ${errorDetail || 'Unknown error occurred'}`;
    }

    return errorDetail || 'An unknown error occurred';
}

// Export functions for use in other modules
window.showError = showError;
window.hideError = hideError;
window.showSuccess = showSuccess;
window.showProgress = showProgress;
window.hideProgress = hideProgress;
window.updateProgress = updateProgress;
window.handleApiResponse = handleApiResponse;