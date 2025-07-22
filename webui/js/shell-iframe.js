/**
 * Dynamic Shell Iframe Component for Gary-Zero Kali Integration
 * 
 * Provides real-time shell visualization with morphism effects and responsive design.
 * Automatically appears when shell operations are executed by the agent.
 */

/**
 * Shell Iframe Manager Class
 * Handles the creation, management, and morphism effects of shell visualization iframes
 */
class ShellIframeManager {
    constructor() {
        this.activeIframes = new Map();
        this.morphismConfig = {
            transparency: 0.15,
            blur: 20,
            borderRadius: '16px',
            shadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        };
        this.initialized = false;
        this.init();
    }

    /**
     * Initialize the shell iframe manager
     */
    init() {
        if (this.initialized) return;
        
        // Listen for shell events from the agent
        this.setupEventListeners();
        
        // Create necessary CSS styles
        this.injectStyles();
        
        this.initialized = true;
        console.log('🛡️ Shell Iframe Manager initialized');
    }

    /**
     * Setup event listeners for shell operations
     */
    setupEventListeners() {
        // Listen for agent shell events
        window.addEventListener('agent_shell_operation_start', (event) => {
            this.handleShellStart(event.detail);
        });

        window.addEventListener('agent_shell_operation_complete', (event) => {
            this.handleShellComplete(event.detail);
        });

        window.addEventListener('agent_shell_operation_error', (event) => {
            this.handleShellError(event.detail);
        });

        window.addEventListener('shell_session_start', (event) => {
            this.handleSessionStart(event.detail);
        });

        window.addEventListener('shell_session_stop', (event) => {
            this.handleSessionStop(event.detail);
        });

        // Handle window resize for responsive design
        window.addEventListener('resize', () => {
            this.updateIframePositions();
        });
    }

    /**
     * Inject necessary CSS styles for morphism and animations
     */
    injectStyles() {
        const styles = `
            .shell-iframe-container {
                position: fixed;
                z-index: 1000;
                transition: all 0.3s ease-out;
                font-family: 'Consolas', 'Monaco', 'Lucida Console', monospace;
            }

            .shell-iframe-glass {
                background: rgba(255, 255, 255, ${this.morphismConfig.transparency});
                backdrop-filter: blur(${this.morphismConfig.blur}px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: ${this.morphismConfig.borderRadius};
                box-shadow: ${this.morphismConfig.shadow};
                padding: 16px;
            }

            .shell-iframe-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                color: #1f2937;
            }

            .shell-iframe-title {
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .shell-iframe-controls {
                display: flex;
                gap: 8px;
                align-items: center;
            }

            .shell-iframe-button {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                padding: 6px 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 14px;
            }

            .shell-iframe-button:hover {
                background: rgba(255, 255, 255, 0.95);
                transform: translateY(-1px);
            }

            .shell-iframe-content {
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            }

            .shell-iframe {
                width: 100%;
                height: 100%;
                border: none;
                background: #000;
                transition: opacity 0.3s ease;
            }

            .shell-iframe-loading {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 200px;
                color: #6b7280;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 12px;
            }

            .shell-iframe-spinner {
                animation: spin 1s linear infinite;
                width: 24px;
                height: 24px;
                border: 2px solid #d1d5db;
                border-top: 2px solid #3b82f6;
                border-radius: 50%;
                margin-right: 12px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .shell-iframe-status {
                margin-top: 8px;
                padding: 8px 12px;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                font-size: 12px;
                color: #6b7280;
            }

            .shell-iframe-enter {
                opacity: 0;
                transform: scale(0.8) translateY(100px);
            }

            .shell-iframe-enter-active {
                opacity: 1;
                transform: scale(1) translateY(0);
            }

            .shell-iframe-exit {
                opacity: 1;
                transform: scale(1) translateY(0);
            }

            .shell-iframe-exit-active {
                opacity: 0;
                transform: scale(0.9) translateY(50px);
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .shell-iframe-container {
                    bottom: 10px !important;
                    right: 10px !important;
                    left: 10px !important;
                    top: auto !important;
                    width: auto !important;
                    height: 50vh !important;
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    /**
     * Handle shell operation start event
     */
    handleShellStart(eventData) {
        const { session_id, command, description, ui_url } = eventData;
        
        this.showShellIframe({
            sessionId: session_id,
            title: `🛡️ Kali Shell - ${description}`,
            url: ui_url,
            command: command,
            status: 'executing'
        });
    }

    /**
     * Handle shell operation completion
     */
    handleShellComplete(eventData) {
        const { session_id, success, execution_time } = eventData;
        
        this.updateIframeStatus(session_id, {
            status: success ? 'completed' : 'failed',
            executionTime: execution_time,
            success: success
        });
    }

    /**
     * Handle shell operation error
     */
    handleShellError(eventData) {
        const { session_id, error } = eventData;
        
        this.updateIframeStatus(session_id, {
            status: 'error',
            error: error
        });
    }

    /**
     * Handle shell session start
     */
    handleSessionStart(eventData) {
        const { id, purpose, ui_url } = eventData;
        
        this.showShellIframe({
            sessionId: id,
            title: `🖥️ Interactive Shell - ${purpose}`,
            url: ui_url,
            status: 'interactive'
        });
    }

    /**
     * Handle shell session stop
     */
    handleSessionStop(eventData) {
        const { id } = eventData;
        this.hideShellIframe(id);
    }

    /**
     * Show shell iframe with morphism effects
     */
    showShellIframe(options) {
        const { sessionId, title, url, command, status } = options;
        
        // Check if iframe already exists
        if (this.activeIframes.has(sessionId)) {
            this.updateExistingIframe(sessionId, options);
            return;
        }

        // Create iframe container
        const container = this.createIframeContainer(sessionId, title, url, command, status);
        
        // Position the iframe
        this.positionIframe(container, sessionId);
        
        // Add to DOM with animation
        document.body.appendChild(container);
        
        // Trigger enter animation
        requestAnimationFrame(() => {
            container.classList.add('shell-iframe-enter-active');
            container.classList.remove('shell-iframe-enter');
        });

        // Store reference
        this.activeIframes.set(sessionId, {
            container,
            url,
            status,
            createdAt: Date.now()
        });

        console.log(`🖥️ Shell iframe created for session: ${sessionId}`);
    }

    /**
     * Create iframe container with all elements
     */
    createIframeContainer(sessionId, title, url, command, status) {
        const container = document.createElement('div');
        container.className = 'shell-iframe-container shell-iframe-enter';
        container.id = `shell-iframe-${sessionId}`;

        const glassContainer = document.createElement('div');
        glassContainer.className = 'shell-iframe-glass';

        // Header
        const header = document.createElement('div');
        header.className = 'shell-iframe-header';

        const titleElement = document.createElement('div');
        titleElement.className = 'shell-iframe-title';
        titleElement.textContent = title;

        const controls = document.createElement('div');
        controls.className = 'shell-iframe-controls';

        // Minimize button
        const minimizeBtn = document.createElement('button');
        minimizeBtn.className = 'shell-iframe-button';
        minimizeBtn.textContent = '−';
        minimizeBtn.title = 'Minimize';
        minimizeBtn.onclick = () => this.minimizeIframe(sessionId);

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'shell-iframe-button';
        closeBtn.textContent = '×';
        closeBtn.title = 'Close';
        closeBtn.onclick = () => this.hideShellIframe(sessionId);

        controls.appendChild(minimizeBtn);
        controls.appendChild(closeBtn);

        header.appendChild(titleElement);
        header.appendChild(controls);

        // Content area
        const content = document.createElement('div');
        content.className = 'shell-iframe-content';

        // Loading state
        const loading = document.createElement('div');
        loading.className = 'shell-iframe-loading';
        loading.innerHTML = `
            <div class="shell-iframe-spinner"></div>
            <span>Connecting to shell...</span>
        `;

        // Iframe
        const iframe = document.createElement('iframe');
        iframe.className = 'shell-iframe';
        iframe.src = url;
        iframe.style.opacity = '0';
        iframe.onload = () => {
            loading.style.display = 'none';
            iframe.style.opacity = '1';
        };

        content.appendChild(loading);
        content.appendChild(iframe);

        // Status bar
        const statusBar = document.createElement('div');
        statusBar.className = 'shell-iframe-status';
        statusBar.textContent = this.getStatusText(status, command);

        glassContainer.appendChild(header);
        glassContainer.appendChild(content);
        glassContainer.appendChild(statusBar);

        container.appendChild(glassContainer);

        return container;
    }

    /**
     * Position iframe responsively
     */
    positionIframe(container, sessionId) {
        const existingCount = this.activeIframes.size;
        const offset = existingCount * 20;

        // Default desktop positioning
        let styles = {
            bottom: `${20 + offset}px`,
            right: `${20 + offset}px`,
            width: '600px',
            height: '400px'
        };

        // Mobile responsive
        if (window.innerWidth <= 768) {
            styles = {
                bottom: '10px',
                left: '10px',
                right: '10px',
                height: '50vh',
                width: 'auto'
            };
        }

        Object.assign(container.style, styles);
    }

    /**
     * Update existing iframe
     */
    updateExistingIframe(sessionId, options) {
        const iframeData = this.activeIframes.get(sessionId);
        if (!iframeData) return;

        const { container } = iframeData;
        const titleElement = container.querySelector('.shell-iframe-title');
        const statusBar = container.querySelector('.shell-iframe-status');

        if (titleElement && options.title) {
            titleElement.textContent = options.title;
        }

        if (statusBar && options.status) {
            statusBar.textContent = this.getStatusText(options.status, options.command);
        }

        // Update stored data
        this.activeIframes.set(sessionId, {
            ...iframeData,
            ...options
        });
    }

    /**
     * Update iframe status
     */
    updateIframeStatus(sessionId, statusData) {
        const iframeData = this.activeIframes.get(sessionId);
        if (!iframeData) return;

        const { container } = iframeData;
        const statusBar = container.querySelector('.shell-iframe-status');

        if (statusBar) {
            let statusText = '';
            if (statusData.status === 'completed') {
                statusText = `✅ Completed in ${statusData.executionTime?.toFixed(2) || 0}s`;
            } else if (statusData.status === 'error') {
                statusText = `❌ Error: ${statusData.error}`;
            } else if (statusData.status === 'failed') {
                statusText = `⚠️ Command failed`;
            }

            statusBar.textContent = statusText;
            statusBar.style.background = statusData.success ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)';
        }
    }

    /**
     * Hide shell iframe
     */
    hideShellIframe(sessionId) {
        const iframeData = this.activeIframes.get(sessionId);
        if (!iframeData) return;

        const { container } = iframeData;
        
        // Exit animation
        container.classList.add('shell-iframe-exit-active');
        container.classList.remove('shell-iframe-exit');

        setTimeout(() => {
            if (container.parentNode) {
                container.parentNode.removeChild(container);
            }
            this.activeIframes.delete(sessionId);
        }, 300);

        console.log(`🖥️ Shell iframe hidden for session: ${sessionId}`);
    }

    /**
     * Minimize iframe
     */
    minimizeIframe(sessionId) {
        const iframeData = this.activeIframes.get(sessionId);
        if (!iframeData) return;

        const { container } = iframeData;
        const content = container.querySelector('.shell-iframe-content');
        const isMinimized = content.style.display === 'none';

        if (isMinimized) {
            content.style.display = 'block';
            container.style.height = '400px';
        } else {
            content.style.display = 'none';
            container.style.height = 'auto';
        }
    }

    /**
     * Update positions for responsive design
     */
    updateIframePositions() {
        this.activeIframes.forEach((iframeData, sessionId) => {
            const { container } = iframeData;
            this.positionIframe(container, sessionId);
        });
    }

    /**
     * Get status text for display
     */
    getStatusText(status, command) {
        switch (status) {
            case 'executing':
                return `⚡ Executing: ${command || 'command'}`;
            case 'interactive':
                return '🖥️ Interactive session active';
            case 'completed':
                return '✅ Command completed';
            case 'error':
                return '❌ Error occurred';
            case 'failed':
                return '⚠️ Command failed';
            default:
                return '🛡️ Shell operation in progress';
        }
    }

    /**
     * Get all active iframes
     */
    getActiveIframes() {
        return Array.from(this.activeIframes.keys());
    }

    /**
     * Close all iframes
     */
    closeAllIframes() {
        const sessionIds = Array.from(this.activeIframes.keys());
        sessionIds.forEach(sessionId => this.hideShellIframe(sessionId));
    }
}

// Initialize shell iframe manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.shellIframeManager = new ShellIframeManager();
    });
} else {
    window.shellIframeManager = new ShellIframeManager();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ShellIframeManager;
}