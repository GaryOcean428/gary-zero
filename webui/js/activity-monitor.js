/**
 * Activity Monitor Integration
 * Provides live activity tracking and integration with the main UI
 */

/* global HTMLIFrameElement */

class ActivityMonitorManager {
    constructor() {
        this.isInitialized = false;
        this.updateInterval = null;
        this.lastActivityCount = 0;
        this.activityTypes = ['browser', 'coding', 'iframe_change'];
        
        // Bind methods
        this.updateActivityCount = this.updateActivityCount.bind(this);
        this.logActivity = this.logActivity.bind(this);
        this.startMonitoring = this.startMonitoring.bind(this);
        this.stopMonitoring = this.stopMonitoring.bind(this);
    }

    async initialize() {
        if (this.isInitialized) return;

        console.log('🔄 Initializing Activity Monitor Manager');

        // Wait for Alpine.js to be ready
        if (typeof Alpine === 'undefined') {
            await this.waitForAlpine();
        }

        // Start activity monitoring
        this.startMonitoring();
        
        // Set up integration with existing systems
        this.setupIntegrations();
        
        this.isInitialized = true;
        console.log('✅ Activity Monitor Manager initialized');
    }

    async waitForAlpine() {
        return new Promise((resolve) => {
            const checkAlpine = () => {
                if (typeof Alpine !== 'undefined' && Alpine.store) {
                    resolve();
                } else {
                    setTimeout(checkAlpine, 100);
                }
            };
            checkAlpine();
        });
    }

    startMonitoring() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Update activity count every 5 seconds
        this.updateInterval = setInterval(this.updateActivityCount, 5000);
        
        // Initial update
        this.updateActivityCount();
    }

    stopMonitoring() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    async updateActivityCount() {
        try {
            const response = await fetch('/activity_monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'get_status'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                const newCount = data.total_activities || 0;
                
                // Update the activity count in the UI
                this.updateUIActivityCount(newCount);
                
                // Show notification for new activities
                if (newCount > this.lastActivityCount) {
                    this.showActivityNotification(newCount - this.lastActivityCount);
                }
                
                this.lastActivityCount = newCount;
            }
        } catch (error) {
            console.warn('Failed to update activity count:', error);
        }
    }

    updateUIActivityCount(count) {
        // Find activity monitor section and update count
        const activitySection = document.querySelector('#activity-monitor-section');
        if (activitySection && typeof Alpine !== 'undefined') {
            // Update Alpine.js data
            const alpineData = Alpine.$data(activitySection);
            if (alpineData) {
                alpineData.activityCount = count;
            }
        }
    }

    showActivityNotification(newActivityCount) {
        // Show toast notification for new activities
        if (window.toastManager && newActivityCount > 0) {
            const message = newActivityCount === 1 
                ? '1 new activity recorded' 
                : `${newActivityCount} new activities recorded`;
            window.toastManager.show(message, 'info', 3000);
        }
    }

    async logActivity(type, description, url = null, data = {}) {
        try {
            const response = await fetch('/activity_monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'add_activity',
                    type: type,
                    description: description,
                    url: url,
                    data: data
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            if (result.success) {
                console.log('📝 Activity logged:', type, description);
                // Trigger immediate update
                this.updateActivityCount();
            }
        } catch (error) {
            console.warn('Failed to log activity:', error);
        }
    }

    setupIntegrations() {
        // Integration with browser activities
        this.setupBrowserIntegration();
        
        // Integration with coding activities (file operations)
        this.setupCodingIntegration();
        
        // Integration with message system
        this.setupMessageIntegration();
    }

    setupBrowserIntegration() {
        // Monitor for iframe src changes
        const originalSetAttribute = HTMLIFrameElement.prototype.setAttribute;
        HTMLIFrameElement.prototype.setAttribute = function(name, value) {
            if (name === 'src' && this.classList.contains('activity-monitor-frame')) {
                window.activityMonitor?.logActivity(
                    'iframe_change',
                    `Activity monitor iframe source changed`,
                    value
                );
            }
            return originalSetAttribute.call(this, name, value);
        };

        // Monitor for external URL loads (if any are implemented)
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            if (typeof url === 'string' && url.startsWith('http') && !url.includes(window.location.hostname)) {
                window.activityMonitor?.logActivity(
                    'browser',
                    `External API call made`,
                    url
                );
            }
            return originalFetch.apply(this, args);
        };
    }

    setupCodingIntegration() {
        // Monitor file operations (if file browser operations are logged)
        const originalFileOperations = ['upload', 'download', 'delete'];
        
        // This would be integrated with existing file browser functionality
        // For now, we'll set up a hook that other parts of the app can use
        window.logCodingActivity = (action, filePath, description = '') => {
            this.logActivity('coding', description || `File ${action}: ${filePath}`, filePath, { action });
        };
    }

    setupMessageIntegration() {
        // Monitor chat messages and responses
        const originalSendMessage = window.sendMessage;
        if (typeof originalSendMessage === 'function') {
            window.sendMessage = async function(...args) {
                const result = await originalSendMessage.apply(this, args);
                window.activityMonitor?.logActivity(
                    'coding',
                    'User sent message to AI',
                    null,
                    { messageLength: args[0]?.length || 0 }
                );
                return result;
            };
        }

        // Monitor AI responses (hook into message display)
        const originalSetMessage = window.setMessage;
        if (typeof originalSetMessage === 'function') {
            window.setMessage = function(id, type, heading, content, temp, kvps) {
                const result = originalSetMessage.apply(this, arguments);
                
                if (type === 'assistant' || type === 'ai') {
                    window.activityMonitor?.logActivity(
                        'coding',
                        'AI response received',
                        null,
                        { messageId: id, contentLength: content?.length || 0 }
                    );
                }
                
                return result;
            };
        }

        // Monitor page navigation
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;
        
        history.pushState = function(...args) {
            const result = originalPushState.apply(this, args);
            window.activityMonitor?.logActivity(
                'browser',
                `Navigation: ${args[2] || window.location.pathname}`,
                window.location.href,
                { action: 'pushState' }
            );
            return result;
        };

        history.replaceState = function(...args) {
            const result = originalReplaceState.apply(this, args);
            window.activityMonitor?.logActivity(
                'browser', 
                `Navigation: ${args[2] || window.location.pathname}`,
                window.location.href,
                { action: 'replaceState' }
            );
            return result;
        };

        // Monitor window focus/blur for activity tracking
        let lastActiveTime = Date.now();
        
        window.addEventListener('focus', () => {
            const inactiveTime = Date.now() - lastActiveTime;
            if (inactiveTime > 30000) { // More than 30 seconds
                window.activityMonitor?.logActivity(
                    'browser',
                    'User returned to application',
                    null,
                    { inactiveTimeMs: inactiveTime }
                );
            }
        });

        window.addEventListener('blur', () => {
            lastActiveTime = Date.now();
            window.activityMonitor?.logActivity(
                'browser',
                'User left application',
                null,
                { timestamp: lastActiveTime }
            );
        });

        // Monitor settings changes
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            const options = args[1];
            
            // Log settings API calls
            if (typeof url === 'string' && url.includes('/settings_')) {
                window.activityMonitor?.logActivity(
                    'coding',
                    `Settings ${url.includes('set') ? 'updated' : 'retrieved'}`,
                    url,
                    { method: options?.method || 'GET' }
                );
            }
            
            // Log external API calls
            if (typeof url === 'string' && url.startsWith('http') && !url.includes(window.location.hostname)) {
                window.activityMonitor?.logActivity(
                    'browser',
                    `External API call: ${new URL(url).hostname}`,
                    url,
                    { method: options?.method || 'GET' }
                );
            }
            
            return originalFetch.apply(this, args);
        };
    }

    // Public API methods
    async clearActivities() {
        try {
            const response = await fetch('/activity_monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'clear_activities'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.lastActivityCount = 0;
                this.updateUIActivityCount(0);
                console.log('🧹 Activities cleared');
            }
            return data.success;
        } catch (error) {
            console.error('Failed to clear activities:', error);
            return false;
        }
    }

    async getActivities(limit = 50, type = null) {
        try {
            const response = await fetch('/activity_monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'get_activities',
                    limit: limit,
                    type: type
                })
            });

            const data = await response.json();
            return data.success ? data.activities : [];
        } catch (error) {
            console.error('Failed to get activities:', error);
            return [];
        }
    }

    destroy() {
        this.stopMonitoring();
        this.isInitialized = false;
        console.log('🛑 Activity Monitor Manager destroyed');
    }
}

// Create global instance
window.activityMonitor = new ActivityMonitorManager();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.activityMonitor.initialize();
    });
} else {
    // DOM is already ready
    window.activityMonitor.initialize();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.activityMonitor) {
        window.activityMonitor.destroy();
    }
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ActivityMonitorManager;
}