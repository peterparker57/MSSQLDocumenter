// Vector store statistics management
class VectorStoreManager {
    constructor() {
        this.tablesCount = document.getElementById('tablesCount');
        this.proceduresCount = document.getElementById('proceduresCount');
        this.functionsCount = document.getElementById('functionsCount');
        this.viewsCount = document.getElementById('viewsCount');
        this.clearBtn = document.getElementById('clearVectorStore');
        
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearVectorStore());
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error('Failed to fetch vector store status');
            }

            const data = await response.json();
            if (data.status === 'success') {
                this.tablesCount.textContent = data.tables_count || 0;
                this.proceduresCount.textContent = data.procedures_count || 0;
                this.functionsCount.textContent = data.functions_count || 0;
                this.viewsCount.textContent = data.views_count || 0;
            } else {
                console.error('Error updating vector stats:', data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error updating vector stats:', error);
            showError('documentationError', 'Error updating vector store statistics: ' + error);
        }
    }

    async clearVectorStore() {
        if (!confirm('Are you sure you want to clear all documentation from the vector store?')) {
            return;
        }

        try {
            const response = await fetch('/api/clear', {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to clear vector store');
            }

            const data = await response.json();
            if (data.status === 'success') {
                // Update stats to show 0
                this.tablesCount.textContent = '0';
                this.proceduresCount.textContent = '0';
                this.functionsCount.textContent = '0';
                this.viewsCount.textContent = '0';
                
                showSuccess('Vector store cleared successfully');
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error clearing vector store:', error);
            showError('documentationError', 'Error clearing vector store: ' + error);
        }
    }
}