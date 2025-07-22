/**
 * Unified AI Action Visualization Manager
 * 
 * Provides comprehensive multi-modal visualization for all AI provider actions
 * including Claude Computer Use, OpenAI Operator, Google AI, browser automation,
 * desktop interactions, and visual computer tasks with real-time streaming.
 */

/**
 * AI Action Visualization Manager Class
 * Extends the existing shell iframe system to handle all types of AI actions
 */
class AIActionVisualizationManager {
    constructor() {
        this.activeVisualizations = new Map();
        this.websocketConnection = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.morphismConfig = {
            transparency: 0.12,
            blur: 24,
            borderRadius: '20px',
            shadow: '0 12px 40px rgba(0, 0, 0, 0.15)'
        };
        this.initialized = false;
        this.actionTypes = {
            'computer_use': '🖥️',
            'browser_automation': '🌐',
            'desktop_interaction': '🖱️',
            'visual_computer_task': '👁️',
            'shell_command': '🛡️',
            'code_execution': '💻',
            'file_operation': '📁',
            'network_request': '🌍',
            'screenshot': '📸',
            'mouse_action': '🖱️',
            'keyboard_action': '⌨️',
            'window_operation': '🪟'
        };
        this.providerColors = {
            'anthropic_claude': '#FF6B35',
            'openai_operator': '#10A37F',
            'google_ai': '#4285F4',
            'gary_zero_native': '#8B5CF6',
            'browser_use': '#059669',
            'kali_shell': '#DC2626'
        };
        this.init();
    }

    /**
     * Initialize the AI action visualization manager
     */
    init() {
        if (this.initialized) return;
        
        console.log('🎯 Initializing AI Action Visualization Manager');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Inject styles
        this.injectStyles();
        
        // Initialize WebSocket connection
        this.initializeWebSocket();
        
        // Setup window management
        this.setupWindowManagement();
        
        this.initialized = true;
        console.log('✅ AI Action Visualization Manager initialized');
    }

    /**
     * Setup event listeners for various AI actions
     */
    setupEventListeners() {
        // Listen for legacy shell events (for backward compatibility)
        window.addEventListener('agent_shell_operation_start', (event) => {
            this.handleLegacyShellEvent('start', event.detail);
        });

        window.addEventListener('agent_shell_operation_complete', (event) => {
            this.handleLegacyShellEvent('complete', event.detail);
        });

        window.addEventListener('agent_shell_operation_error', (event) => {
            this.handleLegacyShellEvent('error', event.detail);
        });

        // Listen for new AI action events
        window.addEventListener('ai_action_detected', (event) => {
            this.handleAIAction(event.detail);
        });

        window.addEventListener('ai_provider_action', (event) => {
            this.handleProviderAction(event.detail);
        });

        // Window management
        window.addEventListener('resize', () => {
            this.updateVisualizationPositions();
        });

        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimations();
            } else {
                this.resumeAnimations();
            }
        });
    }

    /**
     * Initialize WebSocket connection for real-time action streaming
     */
    initializeWebSocket() {
        const wsUrl = this.getWebSocketURL();
        
        try {
            this.websocketConnection = new WebSocket(wsUrl);
            
            this.websocketConnection.onopen = () => {
                console.log('🌐 Connected to AI Action Streaming Service');
                this.reconnectAttempts = 0;
                
                // Subscribe to all action types
                this.subscribeToActions(['all']);
                
                // Request recent action history
                this.requestActionHistory();
            };
            
            this.websocketConnection.onmessage = (event) => {
                this.handleWebSocketMessage(event.data);
            };
            
            this.websocketConnection.onclose = () => {
                console.log('📤 Disconnected from AI Action Streaming Service');
                this.scheduleReconnect();
            };
            
            this.websocketConnection.onerror = (error) => {
                console.error('🚨 WebSocket error:', error);
                this.scheduleReconnect();
            };
            
        } catch (error) {
            console.warn('⚠️ WebSocket not available, falling back to event-based mode');
        }
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.message_type) {
                case 'ai_action':
                    this.visualizeAIAction(message.data);
                    break;
                case 'connection':
                    console.log('🔗 WebSocket connection established:', message.data);
                    break;
                case 'server_stats':
                    this.updateServerStats(message.data);
                    break;
                case 'error':
                    console.error('🚨 Server error:', message.data.message);
                    break;
                default:
                    console.log('📨 Received message:', message);
            }
        } catch (error) {
            console.error('🚨 Failed to parse WebSocket message:', error);
        }
    }

    /**
     * Visualize an AI action
     */
    visualizeAIAction(actionData) {
        const {
            action_id,
            provider,
            action_type,
            description,
            status,
            session_id,
            ui_url,
            screenshot_path,
            agent_name,
            execution_time
        } = actionData;

        // Determine visualization type based on action
        const visualizationType = this.getVisualizationType(action_type, provider);
        
        // Create or update visualization
        this.showActionVisualization({
            actionId: action_id,
            sessionId: session_id || action_id,
            title: this.getActionTitle(provider, action_type, description),
            url: ui_url || this.getActionURL(action_type, session_id),
            type: visualizationType,
            provider: provider,
            actionType: action_type,
            status: status,
            agentName: agent_name,
            executionTime: execution_time,
            screenshotPath: screenshot_path
        });
    }

    /**
     * Show action visualization with morphism effects
     */
    showActionVisualization(options) {
        const {
            actionId,
            sessionId,
            title,
            url,
            type,
            provider,
            actionType,
            status,
            agentName,
            executionTime,
            screenshotPath
        } = options;
        
        // Check if visualization already exists
        if (this.activeVisualizations.has(sessionId)) {
            this.updateExistingVisualization(sessionId, options);
            return;
        }

        // Create visualization container
        const container = this.createVisualizationContainer({
            sessionId,
            title,
            url,
            type,
            provider,
            actionType,
            status,
            agentName,
            screenshotPath
        });
        
        // Position the visualization
        this.positionVisualization(container, sessionId, type);
        
        // Add to DOM with animation
        document.body.appendChild(container);
        
        // Trigger enter animation
        requestAnimationFrame(() => {
            container.classList.add('ai-viz-enter-active');
            container.classList.remove('ai-viz-enter');
        });

        // Store reference
        this.activeVisualizations.set(sessionId, {
            container,
            url,
            type,
            provider,
            actionType,
            status,
            createdAt: Date.now()
        });

        console.log(`🎨 AI Action visualization created: ${title}`);
    }

    /**
     * Create visualization container with all elements
     */
    createVisualizationContainer(options) {
        const {
            sessionId,
            title,
            url,
            type,
            provider,
            actionType,
            status,
            agentName,
            screenshotPath
        } = options;

        const container = document.createElement('div');
        container.className = 'ai-viz-container ai-viz-enter';
        container.id = `ai-viz-${sessionId}`;

        const glassContainer = document.createElement('div');
        glassContainer.className = 'ai-viz-glass';

        // Header with provider-specific styling
        const header = this.createVisualizationHeader(title, provider, actionType, sessionId);
        
        // Content area based on type
        const content = this.createVisualizationContent(type, url, screenshotPath, sessionId);
        
        // Status bar
        const statusBar = this.createStatusBar(status, agentName, provider);
        
        // Controls overlay
        const controls = this.createControlsOverlay(sessionId, type);

        glassContainer.appendChild(header);
        glassContainer.appendChild(content);
        glassContainer.appendChild(statusBar);
        glassContainer.appendChild(controls);
        container.appendChild(glassContainer);

        return container;
    }

    /**
     * Create visualization header
     */
    createVisualizationHeader(title, provider, actionType, sessionId) {
        const header = document.createElement('div');
        header.className = 'ai-viz-header';

        const titleElement = document.createElement('div');
        titleElement.className = 'ai-viz-title';
        
        const icon = this.actionTypes[actionType] || '🤖';
        const providerBadge = this.createProviderBadge(provider);
        
        titleElement.innerHTML = `
            <span class="ai-viz-icon">${icon}</span>
            <span class="ai-viz-title-text">${title}</span>
            ${providerBadge}
        `;

        const controls = document.createElement('div');
        controls.className = 'ai-viz-controls';

        // Action-specific controls
        const actionControls = this.createActionControls(actionType, sessionId);
        
        // Standard controls
        const minimizeBtn = this.createControlButton('−', 'Minimize', () => this.minimizeVisualization(sessionId));
        const popoutBtn = this.createControlButton('⧉', 'Pop out', () => this.popoutVisualization(sessionId));
        const closeBtn = this.createControlButton('×', 'Close', () => this.hideVisualization(sessionId));

        controls.appendChild(actionControls);
        controls.appendChild(minimizeBtn);
        controls.appendChild(popoutBtn);
        controls.appendChild(closeBtn);

        header.appendChild(titleElement);
        header.appendChild(controls);

        return header;
    }

    /**
     * Create visualization content based on type
     */
    createVisualizationContent(type, url, screenshotPath, sessionId) {
        const content = document.createElement('div');
        content.className = 'ai-viz-content';

        switch (type) {
            case 'iframe':
                content.appendChild(this.createIframeContent(url, sessionId));
                break;
            case 'screenshot':
                content.appendChild(this.createScreenshotContent(screenshotPath, sessionId));
                break;
            case 'desktop_mirror':
                content.appendChild(this.createDesktopMirrorContent(sessionId));
                break;
            case 'browser_preview':
                content.appendChild(this.createBrowserPreviewContent(url, sessionId));
                break;
            case 'terminal':
                content.appendChild(this.createTerminalContent(url, sessionId));
                break;
            case 'code_editor':
                content.appendChild(this.createCodeEditorContent(url, sessionId));
                break;
            default:
                content.appendChild(this.createGenericContent(url, sessionId));
        }

        return content;
    }

    /**
     * Create iframe content
     */
    createIframeContent(url, sessionId) {
        const wrapper = document.createElement('div');
        wrapper.className = 'ai-viz-iframe-wrapper';

        const loading = document.createElement('div');
        loading.className = 'ai-viz-loading';
        loading.innerHTML = `
            <div class="ai-viz-spinner"></div>
            <span>Loading AI action interface...</span>
        `;

        const iframe = document.createElement('iframe');
        iframe.className = 'ai-viz-iframe';
        iframe.src = url || 'about:blank';
        iframe.style.opacity = '0';
        
        iframe.onload = () => {
            loading.style.display = 'none';
            iframe.style.opacity = '1';
        };

        iframe.onerror = () => {
            loading.innerHTML = '<span>⚠️ Failed to load interface</span>';
        };

        wrapper.appendChild(loading);
        wrapper.appendChild(iframe);

        return wrapper;
    }

    /**
     * Create screenshot content
     */
    createScreenshotContent(screenshotPath, sessionId) {
        const wrapper = document.createElement('div');
        wrapper.className = 'ai-viz-screenshot-wrapper';

        if (screenshotPath) {
            const img = document.createElement('img');
            img.src = screenshotPath;
            img.className = 'ai-viz-screenshot';
            img.alt = 'AI Action Screenshot';
            
            img.onclick = () => {
                this.openScreenshotModal(screenshotPath);
            };
            
            wrapper.appendChild(img);
        } else {
            wrapper.innerHTML = '<div class="ai-viz-placeholder">📸 Screenshot will appear here</div>';
        }

        return wrapper;
    }

    /**
     * Create desktop mirror content
     */
    createDesktopMirrorContent(sessionId) {
        const wrapper = document.createElement('div');
        wrapper.className = 'ai-viz-desktop-mirror';
        
        // This would connect to a desktop streaming service
        wrapper.innerHTML = `
            <div class="ai-viz-placeholder">
                🖥️ Desktop mirroring active
                <small>Real-time desktop view</small>
            </div>
        `;

        return wrapper;
    }

    /**
     * Create provider badge
     */
    createProviderBadge(provider) {
        const color = this.providerColors[provider] || '#6B7280';
        const name = provider.replace('_', ' ').toUpperCase();
        
        return `<span class="ai-viz-provider-badge" style="background-color: ${color}">${name}</span>`;
    }

    /**
     * Create control button
     */
    createControlButton(text, title, onClick) {
        const button = document.createElement('button');
        button.className = 'ai-viz-button';
        button.textContent = text;
        button.title = title;
        button.onclick = onClick;
        return button;
    }

    /**
     * Get visualization type based on action type and provider
     */
    getVisualizationType(actionType, provider) {
        const typeMap = {
            'computer_use': 'desktop_mirror',
            'browser_automation': 'browser_preview',
            'desktop_interaction': 'desktop_mirror',
            'visual_computer_task': 'screenshot',
            'shell_command': 'terminal',
            'code_execution': 'code_editor',
            'screenshot': 'screenshot'
        };

        return typeMap[actionType] || 'iframe';
    }

    /**
     * Get action title
     */
    getActionTitle(provider, actionType, description) {
        const providerName = provider.replace('_', ' ').split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        
        const actionName = actionType.replace('_', ' ').split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');

        return `${providerName} - ${actionName}`;
    }

    /**
     * Inject comprehensive styles for all visualization types
     */
    injectStyles() {
        const styles = `
            .ai-viz-container {
                position: fixed;
                z-index: 2000;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                min-width: 320px;
                max-width: 90vw;
                max-height: 85vh;
            }

            .ai-viz-glass {
                background: rgba(255, 255, 255, ${this.morphismConfig.transparency});
                backdrop-filter: blur(${this.morphismConfig.blur}px) saturate(180%);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: ${this.morphismConfig.borderRadius};
                box-shadow: ${this.morphismConfig.shadow};
                padding: 16px;
                overflow: hidden;
            }

            .ai-viz-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                color: #1f2937;
            }

            .ai-viz-title {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 16px;
                font-weight: 600;
                flex: 1;
            }

            .ai-viz-icon {
                font-size: 20px;
                filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
            }

            .ai-viz-title-text {
                flex: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .ai-viz-provider-badge {
                font-size: 10px;
                font-weight: 700;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
                letter-spacing: 0.5px;
            }

            .ai-viz-controls {
                display: flex;
                gap: 8px;
                align-items: center;
            }

            .ai-viz-button {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
                padding: 6px 10px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                min-width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .ai-viz-button:hover {
                background: rgba(255, 255, 255, 0.95);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }

            .ai-viz-content {
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                background: rgba(255, 255, 255, 0.5);
                min-height: 200px;
                position: relative;
            }

            .ai-viz-iframe-wrapper, .ai-viz-screenshot-wrapper, 
            .ai-viz-desktop-mirror {
                width: 100%;
                height: 100%;
                position: relative;
                min-height: 300px;
            }

            .ai-viz-iframe {
                width: 100%;
                height: 100%;
                border: none;
                border-radius: 16px;
                transition: opacity 0.3s ease;
                min-height: 300px;
            }

            .ai-viz-screenshot {
                width: 100%;
                height: auto;
                max-height: 400px;
                object-fit: contain;
                border-radius: 12px;
                cursor: pointer;
                transition: transform 0.2s ease;
            }

            .ai-viz-screenshot:hover {
                transform: scale(1.02);
            }

            .ai-viz-loading {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 250px;
                color: #6b7280;
                background: rgba(0, 0, 0, 0.02);
                border-radius: 16px;
                flex-direction: column;
                gap: 12px;
            }

            .ai-viz-spinner {
                animation: spin 1s linear infinite;
                width: 32px;
                height: 32px;
                border: 3px solid #e5e7eb;
                border-top: 3px solid #3b82f6;
                border-radius: 50%;
            }

            .ai-viz-placeholder {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 200px;
                color: #6b7280;
                background: rgba(0, 0, 0, 0.02);
                border-radius: 16px;
                flex-direction: column;
                gap: 8px;
                font-size: 18px;
            }

            .ai-viz-placeholder small {
                font-size: 14px;
                opacity: 0.7;
            }

            .ai-viz-status {
                margin-top: 12px;
                padding: 8px 16px;
                background: rgba(0, 0, 0, 0.03);
                border-radius: 12px;
                font-size: 12px;
                color: #6b7280;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .ai-viz-status-info {
                display: flex;
                gap: 16px;
                align-items: center;
            }

            .ai-viz-status-badge {
                padding: 2px 8px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .ai-viz-status-badge.started { background: #dbeafe; color: #1e40af; }
            .ai-viz-status-badge.completed { background: #dcfce7; color: #15803d; }
            .ai-viz-status-badge.failed { background: #fee2e2; color: #dc2626; }
            .ai-viz-status-badge.error { background: #fef2f2; color: #b91c1c; }

            /* Animations */
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .ai-viz-enter {
                opacity: 0;
                transform: scale(0.8) translateY(40px);
            }

            .ai-viz-enter-active {
                opacity: 1;
                transform: scale(1) translateY(0);
            }

            .ai-viz-exit {
                opacity: 1;
                transform: scale(1) translateY(0);
            }

            .ai-viz-exit-active {
                opacity: 0;
                transform: scale(0.9) translateY(20px);
            }

            /* Multi-modal layout */
            .ai-viz-grid {
                position: fixed;
                top: 20px;
                right: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 16px;
                max-width: 1200px;
                z-index: 1999;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .ai-viz-container {
                    bottom: 10px !important;
                    right: 10px !important;
                    left: 10px !important;
                    top: auto !important;
                    width: auto !important;
                    height: 60vh !important;
                    max-height: 60vh !important;
                }

                .ai-viz-content {
                    min-height: 150px;
                }

                .ai-viz-iframe {
                    min-height: 200px;
                }
            }

            /* Dark mode support */
            @media (prefers-color-scheme: dark) {
                .ai-viz-glass {
                    background: rgba(17, 24, 39, 0.8);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }

                .ai-viz-header, .ai-viz-status {
                    color: #f9fafb;
                }

                .ai-viz-button {
                    background: rgba(0, 0, 0, 0.3);
                    color: #f9fafb;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }

                .ai-viz-content {
                    background: rgba(0, 0, 0, 0.2);
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    /**
     * Get WebSocket URL for streaming connection
     */
    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = 8765; // Default streaming port
        return `${protocol}//${host}:${port}`;
    }

    /**
     * Subscribe to action types via WebSocket
     */
    subscribeToActions(subscriptions) {
        if (this.websocketConnection && this.websocketConnection.readyState === WebSocket.OPEN) {
            const message = {
                type: 'subscribe',
                subscriptions: subscriptions
            };
            this.websocketConnection.send(JSON.stringify(message));
        }
    }

    /**
     * Request action history
     */
    requestActionHistory() {
        if (this.websocketConnection && this.websocketConnection.readyState === WebSocket.OPEN) {
            const message = {
                type: 'get_history',
                limit: 20
            };
            this.websocketConnection.send(JSON.stringify(message));
        }
    }

    /**
     * Schedule WebSocket reconnection
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('🚨 Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            this.initializeWebSocket();
        }, delay);
    }

    /**
     * Position visualization based on type and existing visualizations
     */
    positionVisualization(container, sessionId, type) {
        const existingCount = this.activeVisualizations.size;
        const offset = existingCount * 20;

        // Calculate position based on type
        let position = this.calculatePosition(type, existingCount);

        Object.assign(container.style, position);
    }

    /**
     * Calculate position for visualization
     */
    calculatePosition(type, existingCount) {
        const offset = existingCount * 20;
        
        // Type-specific positioning
        switch (type) {
            case 'desktop_mirror':
                return {
                    top: `${20 + offset}px`,
                    left: `${20 + offset}px`,
                    width: '500px',
                    height: '400px'
                };
            case 'browser_preview':
                return {
                    top: `${20 + offset}px`,
                    right: `${20 + offset}px`,
                    width: '600px',
                    height: '450px'
                };
            case 'terminal':
                return {
                    bottom: `${20 + offset}px`,
                    right: `${20 + offset}px`,
                    width: '600px',
                    height: '350px'
                };
            case 'screenshot':
                return {
                    top: `${20 + offset}px`,
                    right: `${320 + offset}px`,
                    width: '300px',
                    height: 'auto'
                };
            default:
                return {
                    bottom: `${20 + offset}px`,
                    right: `${20 + offset}px`,
                    width: '500px',
                    height: '400px'
                };
        }
    }

    /**
     * Handle legacy shell events for backward compatibility
     */
    handleLegacyShellEvent(eventType, eventData) {
        const legacyAction = {
            action_id: eventData.session_id || 'legacy',
            provider: 'kali_shell',
            action_type: 'shell_command',
            description: eventData.description || eventData.command || 'Shell operation',
            status: eventType === 'start' ? 'started' : eventType,
            session_id: eventData.session_id,
            ui_url: eventData.ui_url,
            agent_name: 'Kali Shell Agent',
            execution_time: eventData.execution_time
        };

        this.visualizeAIAction(legacyAction);
    }

    /**
     * Update existing visualization
     */
    updateExistingVisualization(sessionId, options) {
        const vizData = this.activeVisualizations.get(sessionId);
        if (!vizData) return;

        const { container } = vizData;
        
        // Update title
        const titleElement = container.querySelector('.ai-viz-title-text');
        if (titleElement && options.title) {
            titleElement.textContent = options.title;
        }

        // Update status
        this.updateVisualizationStatus(sessionId, options);

        // Update stored data
        this.activeVisualizations.set(sessionId, {
            ...vizData,
            ...options
        });
    }

    /**
     * Update visualization status
     */
    updateVisualizationStatus(sessionId, statusData) {
        const vizData = this.activeVisualizations.get(sessionId);
        if (!vizData) return;

        const { container } = vizData;
        const statusBar = container.querySelector('.ai-viz-status');

        if (statusBar) {
            statusBar.innerHTML = this.createStatusContent(statusData);
        }
    }

    /**
     * Create status content
     */
    createStatusContent(statusData) {
        const { status, agentName, executionTime, provider } = statusData;
        
        const statusBadge = `<span class="ai-viz-status-badge ${status}">${status}</span>`;
        const agentInfo = agentName ? `Agent: ${agentName}` : '';
        const timeInfo = executionTime ? `${executionTime.toFixed(2)}s` : '';
        
        return `
            <div class="ai-viz-status-info">
                ${statusBadge}
                <span>${agentInfo}</span>
                ${timeInfo ? `<span>${timeInfo}</span>` : ''}
            </div>
        `;
    }

    /**
     * Hide visualization
     */
    hideVisualization(sessionId) {
        const vizData = this.activeVisualizations.get(sessionId);
        if (!vizData) return;

        const { container } = vizData;
        
        // Exit animation
        container.classList.add('ai-viz-exit-active');
        container.classList.remove('ai-viz-exit');

        setTimeout(() => {
            if (container.parentNode) {
                container.parentNode.removeChild(container);
            }
            this.activeVisualizations.delete(sessionId);
        }, 400);

        console.log(`🎨 AI Action visualization hidden: ${sessionId}`);
    }

    /**
     * Minimize visualization
     */
    minimizeVisualization(sessionId) {
        const vizData = this.activeVisualizations.get(sessionId);
        if (!vizData) return;

        const { container } = vizData;
        const content = container.querySelector('.ai-viz-content');
        const isMinimized = content.style.display === 'none';

        if (isMinimized) {
            content.style.display = 'block';
            container.style.height = this.calculatePosition(vizData.type, 0).height;
        } else {
            content.style.display = 'none';
            container.style.height = 'auto';
        }
    }

    /**
     * Pop out visualization to new window
     */
    popoutVisualization(sessionId) {
        const vizData = this.activeVisualizations.get(sessionId);
        if (!vizData) return;

        const { url, type } = vizData;
        if (url) {
            const popoutWindow = window.open(
                url,
                `ai_viz_${sessionId}`,
                'width=800,height=600,scrollbars=yes,resizable=yes'
            );
            
            if (popoutWindow) {
                this.hideVisualization(sessionId);
            }
        }
    }

    /**
     * Update all visualization positions
     */
    updateVisualizationPositions() {
        this.activeVisualizations.forEach((vizData, sessionId) => {
            const { container, type } = vizData;
            const position = this.calculatePosition(type, 0);
            Object.assign(container.style, position);
        });
    }

    /**
     * Get all active visualizations
     */
    getActiveVisualizations() {
        return Array.from(this.activeVisualizations.keys());
    }

    /**
     * Close all visualizations
     */
    closeAllVisualizations() {
        const sessionIds = Array.from(this.activeVisualizations.keys());
        sessionIds.forEach(sessionId => this.hideVisualization(sessionId));
    }

    /**
     * Setup window management for multiple visualizations
     */
    setupWindowManagement() {
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.updateVisualizationPositions();
            }, 100);
        });

        // Handle window focus/blur for optimization
        window.addEventListener('focus', () => {
            this.resumeAnimations();
        });

        window.addEventListener('blur', () => {
            this.pauseAnimations();
        });
    }

    /**
     * Pause animations for performance
     */
    pauseAnimations() {
        document.body.classList.add('ai-viz-animations-paused');
    }

    /**
     * Resume animations
     */
    resumeAnimations() {
        document.body.classList.remove('ai-viz-animations-paused');
    }
}

// Initialize AI Action Visualization Manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.aiActionVisualizationManager = new AIActionVisualizationManager();
    });
} else {
    window.aiActionVisualizationManager = new AIActionVisualizationManager();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIActionVisualizationManager;
}