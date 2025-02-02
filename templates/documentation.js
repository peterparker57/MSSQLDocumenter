// Handle documentation tab functionality
class DocumentationManager {
    constructor() {
        // Get tab elements
        this.documentationTab = document.getElementById('documentation-tab');
        this.documentationContent = document.getElementById('documentation');
        
        // Get card elements
        this.optionsCard = document.getElementById('optionsCard');
        this.searchCard = document.getElementById('searchCard');
        this.progressCard = document.getElementById('progressCard');
        
        // Initialize tab event listeners
        if (this.documentationTab) {
            this.documentationTab.addEventListener('shown.bs.tab', () => this.onTabShown());
        }
    }
    
    onTabShown() {
        // Show documentation cards if connected
        if (window.appState.connected) {
            this.optionsCard.style.display = 'block';
            this.searchCard.style.display = 'block';
            if (window.appState.documenting) {
                this.progressCard.style.display = 'block';
            }
        }
    }
}

// Initialize documentation manager
document.addEventListener('DOMContentLoaded', () => {
    window.documentationManager = new DocumentationManager();
});