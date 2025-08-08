/* global Logger */

// Create logger instance for settings module
const logger = window.Logger ? new Logger('Settings') : { 
    debug: console.log, 
    info: console.info, 
    warn: console.warn, 
    error: console.error 
};

// Utility function for debouncing
function debounce(func, wait, options = {}) {
    let timeout;
    let result;
    let lastArgs;
    let lastThis;
    let maxTimeoutId;
    let lastCallTime;
    
    const leading = !!options.leading;
    const trailing = options.trailing !== false;
    const maxWait = options.maxWait;
    
    function invokeFunc(time) {
        const args = lastArgs;
        const thisArg = lastThis;
        
        lastArgs = lastThis = undefined;
        result = func.apply(thisArg, args);
        return result;
    }
    
    function startTimer(pendingFunc, wait) {
        return setTimeout(pendingFunc, wait);
    }
    
    function cancelTimer(id) {
        clearTimeout(id);
    }
    
    function leadingEdge(time) {
        lastCallTime = time;
        timeout = startTimer(timerExpired, wait);
        return leading ? invokeFunc(time) : result;
    }
    
    function remainingWait(time) {
        const timeSinceLastCall = time - lastCallTime;
        const timeSinceLastInvoke = time - (lastCallTime || 0);
        const timeWaiting = wait - timeSinceLastCall;
        
        return maxWait !== undefined ? Math.min(timeWaiting, maxWait - timeSinceLastInvoke) : timeWaiting;
    }
    
    function shouldInvoke(time) {
        const timeSinceLastCall = time - lastCallTime;
        const timeSinceLastInvoke = time - (lastCallTime || 0);
        
        return (lastCallTime === undefined || (timeSinceLastCall >= wait) ||
                (timeSinceLastCall < 0) || (maxWait !== undefined && timeSinceLastInvoke >= maxWait));
    }
    
    function timerExpired() {
        const time = Date.now();
        if (shouldInvoke(time)) {
            return trailingEdge(time);
        }
        timeout = startTimer(timerExpired, remainingWait(time));
    }
    
    function trailingEdge(time) {
        timeout = undefined;
        
        if (trailing && lastArgs) {
            return invokeFunc(time);
        }
        lastArgs = lastThis = undefined;
        return result;
    }
    
    function debounced(...args) {
        const time = Date.now();
        const isInvoking = shouldInvoke(time);
        
        lastArgs = args;
        lastThis = this;
        lastCallTime = time;
        
        if (isInvoking) {
            if (timeout === undefined) {
                return leadingEdge(lastCallTime);
            }
            if (maxWait !== undefined) {
                timeout = startTimer(timerExpired, wait);
                return invokeFunc(lastCallTime);
            }
        }
        if (timeout === undefined) {
            timeout = startTimer(timerExpired, wait);
        }
        return result;
    }
    
    debounced.cancel = function() {
        if (timeout !== undefined) {
            cancelTimer(timeout);
        }
        if (maxTimeoutId !== undefined) {
            cancelTimer(maxTimeoutId);
        }
        lastCallTime = 0;
        lastArgs = lastThis = timeout = maxTimeoutId = undefined;
    };
    
    return debounced;
}

const settingsModalProxy = {
    isOpen: false,
    settings: {},
    resolvePromise: null,
    activeTab: "agent", // Default tab
    provider: "serveo",
    isLoading: false,

    // Computed property for filtered sections
    get filteredSections() {
        if (!this.settings || !this.settings.sections) return [];
        const filteredSections = this.settings.sections.filter((section) => section.tab === this.activeTab);

        // If no sections match the current tab (or all tabs are missing), show all sections
        if (filteredSections.length === 0) {
            return this.settings.sections;
        }

        return filteredSections;
    },

    // Initialize debounced save function
    init() {
        if (!this._debouncedSaveSettings) {
            this._debouncedSaveSettings = debounce(this._actualSaveSettings.bind(this), 1000, { trailing: true });
        }
    },

    // Switch tab method
    switchTab(tabName) {
        // Update our component state
        this.activeTab = tabName;

        // Update the store safely with retry logic
        try {
            const store = Alpine.store("root");
            if (store) {
                store.activeTab = tabName;
            } else {
                logger.warn("Root store not available during tab switch, will retry");
                // Retry after a short delay if store not ready
                setTimeout(() => {
                    const retryStore = Alpine.store("root");
                    if (retryStore) {
                        retryStore.activeTab = tabName;
                    }
                }, 100);
            }
        } catch (error) {
            logger.warn("Error accessing Alpine store during tab switch:", error);
        }

        localStorage.setItem("settingsActiveTab", tabName);

        // Auto-scroll active tab into view after a short delay to ensure DOM updates
        setTimeout(() => {
            const activeTab = document.querySelector(".settings-tab.active");
            if (activeTab) {
                activeTab.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
            }

            // When switching to the scheduler tab, initialize Flatpickr components
            if (tabName === "scheduler") {
                logger.info("Switching to scheduler tab, initializing Flatpickr");
                const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                if (schedulerElement) {
                    const schedulerData = Alpine.$data(schedulerElement);
                    if (schedulerData) {
                        // Start polling
                        if (typeof schedulerData.startPolling === "function") {
                            schedulerData.startPolling();
                        }

                        // Initialize Flatpickr if editing or creating
                        if (typeof schedulerData.initFlatpickr === "function") {
                            // Check if we're creating or editing and initialize accordingly
                            if (schedulerData.isCreating) {
                                schedulerData.initFlatpickr("create");
                            } else if (schedulerData.isEditing) {
                                schedulerData.initFlatpickr("edit");
                            }
                        }

                        // Force an immediate fetch
                        if (typeof schedulerData.fetchTasks === "function") {
                            schedulerData.fetchTasks();
                        }
                    }
                }
            }

            // When switching to the tunnel tab, initialize tunnelSettings
            if (tabName === "tunnel") {
                logger.info("Switching to tunnel tab, initializing tunnelSettings");
                const tunnelElement = document.querySelector('[x-data="tunnelSettings"]');
                if (tunnelElement) {
                    const tunnelData = Alpine.$data(tunnelElement);
                    if (tunnelData && typeof tunnelData.checkTunnelStatus === "function") {
                        // Check tunnel status
                        tunnelData.checkTunnelStatus();
                    }
                }
            }
        }, 10);
    },

    async openModal() {
        logger.info("Settings modal opening");
        const modalEl = document.getElementById("settingsModal");
        if (!modalEl) {
            logger.error("Settings modal element not found");
            return;
        }

        // Wait for Alpine to be ready and ensure component is initialized
        if (typeof Alpine === "undefined") {
            logger.error("Alpine.js not available");
            return;
        }

        let modalAD = null;
        try {
            // Try to get the Alpine data, with retries for timing issues
            for (let i = 0; i < 5; i++) {
                try {
                    modalAD = Alpine.$data(modalEl);
                    // Enhanced validation for Alpine data
                    if (modalAD && (modalAD._x_dataStack || modalAD.isOpen !== undefined)) {
                        break;
                    }
                } catch (dataError) {
                    logger.warn(`Attempt ${i + 1}: Error getting Alpine data:`, dataError.message);
                }
                // Wait progressively longer
                await new Promise((resolve) => setTimeout(resolve, 100 * (i + 1)));
            }

            if (!modalAD) {
                logger.error("Settings modal not properly initialized with Alpine.js");
                return;
            }
        } catch (error) {
            logger.error("Error accessing Alpine data:", error);
            return;
        }

        // First, ensure the store is updated properly with proper error handling
        let store = null;
        try {
            // Wait for Alpine to be fully ready
            if (typeof Alpine === 'undefined') {
                logger.warn("Alpine.js not yet loaded, delaying settings modal open");
                setTimeout(() => this.openSettings(), 100);
                return new Promise((resolve) => { this.resolvePromise = resolve; });
            }
            
            store = Alpine.store("root");
            if (store) {
                // Set isOpen first to ensure proper state
                store.isOpen = true;
            } else {
                logger.warn("Root store not found, will retry initialization");
                // Retry after Alpine is fully ready
                setTimeout(() => {
                    const retryStore = Alpine.store("root");
                    if (retryStore) {
                        retryStore.isOpen = true;
                    }
                }, 100);
            }
        } catch (error) {
            logger.error("Error accessing Alpine store:", error);
        }

        //get settings from backend
        try {
            logger.info("Fetching settings from /settings_get endpoint");
            const set = await sendJsonData("/settings_get", {});
            logger.info("Settings fetch successful:", set);

            // First load the settings data without setting the active tab
            const settings = {
                title: "Settings",
                buttons: [
                    {
                        id: "save",
                        title: "Save",
                        classes: "btn btn-ok",
                    },
                    {
                        id: "cancel",
                        title: "Cancel",
                        type: "secondary",
                        classes: "btn btn-cancel",
                    },
                ],
                sections: set.settings.sections,
            };

            // Update modal data
            modalAD.isOpen = true;
            modalAD.settings = settings;

            // Now set the active tab after the modal is open
            // This ensures Alpine reactivity works as expected
            setTimeout(() => {
                // Get stored tab or default to 'agent'
                const savedTab = localStorage.getItem("settingsActiveTab") || "agent";
                logger.info(`Setting initial tab to: ${savedTab}`);

                // Directly set the active tab
                modalAD.activeTab = savedTab;

                // Also update the store
                if (store) {
                    store.activeTab = savedTab;
                }

                localStorage.setItem("settingsActiveTab", savedTab);

                // Add a small delay *after* setting the tab to ensure scrolling works
                setTimeout(() => {
                    const activeTabElement = document.querySelector(".settings-tab.active");
                    if (activeTabElement) {
                        activeTabElement.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
                    }
                    // Debug log
                    const schedulerTab = document.querySelector('.settings-tab[title="Task Scheduler"]');
                    logger.debug(`Current active tab after direct set: ${modalAD.activeTab}`);
                    logger.debug(
                        "Scheduler tab active after direct initialization?",
                        schedulerTab && schedulerTab.classList.contains("active")
                    );

                    // Explicitly start polling if we're on the scheduler tab
                    if (modalAD.activeTab === "scheduler") {
                        logger.info("Settings opened directly to scheduler tab, initializing polling");
                        const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                        if (schedulerElement) {
                            const schedulerData = Alpine.$data(schedulerElement);
                            if (schedulerData && typeof schedulerData.startPolling === "function") {
                                schedulerData.startPolling();
                                // Also force an immediate fetch
                                if (typeof schedulerData.fetchTasks === "function") {
                                    schedulerData.fetchTasks();
                                }
                            }
                        }
                    }
                }, 10); // Small delay just for scrolling
            }, 5); // Keep a minimal delay for modal opening reactivity

            // Add a watcher to disable the Save button when a task is being created or edited
            const schedulerComponent = document.querySelector('[x-data="schedulerSettings"]');
            if (schedulerComponent) {
                // Watch for changes to the scheduler's editing state
                const checkSchedulerEditingState = () => {
                    const schedulerData = Alpine.$data(schedulerComponent);
                    if (schedulerData) {
                        // If we're on the scheduler tab and creating/editing a task, disable the Save button
                        const saveButton = document.querySelector(".modal-footer button.btn-ok");
                        if (
                            saveButton &&
                            modalAD.activeTab === "scheduler" &&
                            (schedulerData.isCreating || schedulerData.isEditing)
                        ) {
                            saveButton.disabled = true;
                            saveButton.classList.add("btn-disabled");
                        } else if (saveButton) {
                            saveButton.disabled = false;
                            saveButton.classList.remove("btn-disabled");
                        }
                    }
                };

                // Add a mutation observer to detect changes in the scheduler component's state
                const observer = new MutationObserver(checkSchedulerEditingState);
                observer.observe(schedulerComponent, { attributes: true, subtree: true, childList: true });

                // Also watch for tab changes to update button state
                modalAD.$watch("activeTab", checkSchedulerEditingState);

                // Initial check
                setTimeout(checkSchedulerEditingState, 100);
            }

            return new Promise((resolve) => {
                this.resolvePromise = resolve;
            });
        } catch (e) {
            window.toastFetchError("Error getting settings", e);
        }
    },

    async handleButton(buttonId) {
        if (buttonId === "save") {
            const modalEl = document.getElementById("settingsModal");
            const modalAD = Alpine.$data(modalEl);
            let resp;
            try {
                resp = await window.sendJsonData("/settings_set", modalAD.settings);
            } catch (e) {
                window.toastFetchError("Error saving settings", e);
                return;
            }
            document.dispatchEvent(new CustomEvent("settings-updated", { detail: resp.settings }));
            this.resolvePromise({
                status: "saved",
                data: resp.settings,
            });
        } else if (buttonId === "cancel") {
            this.handleCancel();
        }

        // Stop scheduler polling if it's running
        this.stopSchedulerPolling();

        // First update our component state
        this.isOpen = false;

        // Then safely update the store
        const store = Alpine.store("root");
        if (store) {
            // Use a slight delay to avoid reactivity issues
            setTimeout(() => {
                store.isOpen = false;
            }, 10);
        }
    },

    async handleCancel() {
        this.resolvePromise({
            status: "cancelled",
            data: null,
        });

        // Stop scheduler polling if it's running
        this.stopSchedulerPolling();

        // First update our component state
        this.isOpen = false;

        // Then safely update the store
        const store = Alpine.store("root");
        if (store) {
            // Use a slight delay to avoid reactivity issues
            setTimeout(() => {
                store.isOpen = false;
            }, 10);
        }
    },

    // Add a helper method to stop scheduler polling
    stopSchedulerPolling() {
        // Find the scheduler component and stop polling if it exists
        const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
        if (schedulerElement) {
            const schedulerData = Alpine.$data(schedulerElement);
            if (schedulerData && typeof schedulerData.stopPolling === "function") {
                logger.info("Stopping scheduler polling on modal close");
                schedulerData.stopPolling();
            }
        }
    },

    async handleFieldButton(field) {
        logger.debug(`Button clicked: ${field.id}`);

        if (field.id === "mcp_servers_config") {
            openModal("settings/mcp/client/mcp-servers.html");
        }
    },

    // Handle provider change for model filtering
            async handleProviderChange(providerId, newProvider) {
                try {
                    logger.info(`Provider changed: ${providerId} to ${newProvider}`);
                    
                    const showDeprecated = localStorage.getItem('showDeprecated') === 'true';

                    // Get the new models for this provider
                    const response = await fetch("/get_models_for_provider", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ provider: newProvider, show_deprecated: showDeprecated }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const models = data.models || [];
                                
                                // Add release date tooltips to model options
                                const enhancedModels = models.map(model => {
                                    const enhanced = { ...model };
                                    if (model.release_date) {
                                        enhanced.tooltip = `Released: ${model.release_date}`;
                                    }
                                    return enhanced;
                                });
                                
                                // Find the corresponding model name field and update its options
                                const modelFieldId = providerId.replace('_provider', '_name');
                                
                                // Get the current modal data
                                const modalEl = document.getElementById("settingsModal");
                                if (modalEl) {
                                    const modalAD = Alpine.$data(modalEl);
                                    if (modalAD && modalAD.settings && modalAD.settings.sections) {
                                        for (const section of modalAD.settings.sections) {
                                            for (const field of section.fields) {
                                                if (field.id === modelFieldId) {
                                                    field.options = enhancedModels;
                                                    // Reset the model value if current value is not in new options
                                                    const currentValueExists = enhancedModels.some(model => model.value === field.value);
                                                    if (!currentValueExists && enhancedModels.length > 0) {
                                                        field.value = enhancedModels[0].value; // Set to first available model
                                                        
                                                        // Auto-update model parameters when model changes
                                                        await this.handleModelChange(modelFieldId, field.value, newProvider);
                                                    }
                                                    logger.info(`Updated ${modelFieldId} with ${enhancedModels.length} models`);
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
            } else {
                logger.error("Failed to fetch models for provider:", response.status);
            }
        } catch (error) {
            logger.error("Error handling provider change:", error);
        }
    },

    // Handle model change for automatic parameter updates
    async handleModelChange(modelFieldId, newModel, provider) {
        try {
            logger.info(`Model changed: ${modelFieldId} to ${newModel} (provider: ${provider})`);
            
            // Get parameters for this model
            const response = await fetch("/get_model_parameters", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ 
                    provider: provider, 
                    model_name: newModel 
                }),
            });

            if (response.ok) {
                const data = await response.json();
                const parameters = data.parameters || {};
                
                logger.debug(`Received parameters for ${newModel}:`, parameters);
                
                // Update related parameter fields
                const modalEl = document.getElementById("settingsModal");
                if (modalEl) {
                    const modalAD = Alpine.$data(modalEl);
                    if (modalAD && modalAD.settings && modalAD.settings.sections) {
                        const baseId = modelFieldId.replace('_name', '');
                        
                        // Map of parameter keys to field suffixes
                        const parameterMapping = {
                            'ctx_length': '_ctx_length',
                            'vision': '_vision',
                            'rl_requests': '_rl_requests',
                            'rl_input': '_rl_input',
                            'rl_output': '_rl_output'
                        };
                        
                        for (const section of modalAD.settings.sections) {
                            for (const field of section.fields) {
                                // Check if this field corresponds to a model parameter
                                for (const [paramKey, fieldSuffix] of Object.entries(parameterMapping)) {
                                    if (field.id === baseId + fieldSuffix && Object.prototype.hasOwnProperty.call(parameters, paramKey)) {
                                        const oldValue = field.value;
                                        field.value = parameters[paramKey];
                                        logger.debug(`Updated ${field.id}: ${oldValue} → ${field.value}`);
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                logger.error("Failed to fetch model parameters:", response.status);
            }
        } catch (error) {
            logger.error("Error handling model change:", error);
        }
    },
};

// function initSettingsModal() {

//     window.openSettings = function () {
//         proxy.openModal().then(result => {
//             console.log(result);  // This will log the result when the modal is closed
//         });
//     }

//     return proxy
// }

// document.addEventListener('alpine:init', () => {
//     Alpine.store('settingsModal', initSettingsModal());
// });

document.addEventListener("alpine:init", () => {
    // Root store is now initialized in initFw.js for better timing
    
    // Initialize settings modal Alpine component using the Component Manager
    if (window.safeRegisterAlpineComponent) {
        window.safeRegisterAlpineComponent("settingsModal", () => ({
            settingsData: {},
            filteredSections: [],
            activeTab: "agent",
            isLoading: true,
            envStatus: null, // Add environment variable status

            async init() {
                try {
                    // Wait for root store to be available with retry logic
                    let rootStore = null;
                    let retryCount = 0;
                    const maxRetries = 10;
                    
                    // Add listener for deprecated toggle
                    document.addEventListener('deprecated-toggle-changed', () => {
                        this.refreshAllModels();
                    });
                    
                    while (!rootStore && retryCount < maxRetries) {
                        try {
                            rootStore = Alpine.store("root");
                            if (rootStore) break;
                        } catch {
                            logger.warn(`Retry ${retryCount + 1}: Root store not ready yet`);
                        }
                        await new Promise(resolve => setTimeout(resolve, 50));
                        retryCount++;
                    }
                    
                    if (rootStore) {
                        this.activeTab = rootStore.activeTab || "agent";
                    } else {
                        logger.warn("Root store not available after retries, using default");
                        this.activeTab = "agent";
                    }
                    if (rootStore) {
                        this.activeTab = rootStore.activeTab || "agent";
                    } else {
                        logger.warn("Root store not available after retries, using default");
                        this.activeTab = "agent";
                    }

                    // Watch store tab changes with null safety
                    this.$watch("$store.root.activeTab", (newTab) => {
                        if (typeof newTab !== "undefined" && newTab !== null) {
                            this.activeTab = newTab;
                            localStorage.setItem("settingsActiveTab", newTab);
                            this.updateFilteredSections();
                        }
                    });

                    // Load settings and environment variable status
                    await this.fetchSettings();
                    await this.fetchEnvStatus();
                    this.updateFilteredSections();
                } catch (error) {
                    logger.error("Error in settingsModal init:", error);
                    // Set fallback state
                    this.activeTab = "agent";
                    this.isLoading = false;
                }
            },

            switchTab(tab) {
                try {
                    // Update our component state
                    this.activeTab = tab;

                    // Update the store safely with retry logic
                    try {
                        const store = Alpine.store("root");
                        if (store) {
                            store.activeTab = tab;
                        } else {
                            logger.warn("Root store not available during tab switch, will retry");
                            // Retry after a short delay if store not ready
                            setTimeout(() => {
                                const retryStore = Alpine.store("root");
                                if (retryStore) {
                                    retryStore.activeTab = tab;
                                }
                            }, 100);
                        }
                    } catch (error) {
                        logger.warn("Error accessing Alpine store during tab switch:", error);
                    }

                    // Save to localStorage
                    localStorage.setItem("settingsActiveTab", tab);

                    // Update filtered sections
                    this.updateFilteredSections();
                } catch (error) {
                    logger.error("Error switching tab:", error);
                }
            },

            async fetchSettings() {
                try {
                    this.isLoading = true;
                    logger.info("Fetching settings from /settings_get endpoint");
                    const response = await fetch("/settings_get", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({}),
                    });

                    logger.info("Settings response status:", response.status, response.statusText);
                    if (response.ok) {
                        const data = await response.json();
                        logger.info("Settings data received:", data);
                        if (data && data.settings) {
                            this.settingsData = data.settings;
                        } else {
                            logger.error("Invalid settings data format:", data);
                        }
                    } else {
                        const errorText = await response.text();
                        logger.error("Failed to fetch settings:", response.status, response.statusText, errorText);
                    }
                } catch (error) {
                    logger.error("Error fetching settings:", error);
                } finally {
                    this.isLoading = false;
                }
            },

            async fetchEnvStatus() {
                try {
                    logger.info("Fetching environment variable status from /env_status endpoint");
                    const response = await fetch("/env_status", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({}),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        logger.info("Environment status data received:", data);
                        this.envStatus = data.env_status || null;
                    } else {
                        logger.warn("Failed to fetch environment status:", response.status, response.statusText);
                        this.envStatus = null;
                    }
                } catch (error) {
                    logger.warn("Error fetching environment status:", error);
                    this.envStatus = null;
                }
            },

            // Check if a field is overridden by environment variables
            isFieldOverriddenByEnv(fieldId) {
                if (!this.envStatus || !this.envStatus.overridden) {
                    return false;
                }
                
                // Check direct field override
                if (this.envStatus.overridden[fieldId]) {
                    return true;
                }
                
                // Check API key overrides
                if (fieldId.startsWith('api_key_')) {
                    const provider = fieldId.replace('api_key_', '').toUpperCase();
                    return this.envStatus.overridden[`api_keys.${provider}`];
                }
                
                return false;
            },

            // Get environment variable name for a field
            getEnvVarName(fieldId) {
                if (!this.envStatus || !this.envStatus.overridden) {
                    return null;
                }
                
                const override = this.envStatus.overridden[fieldId];
                if (override) {
                    return override.env_var;
                }
                
                // Check API key overrides
                if (fieldId.startsWith('api_key_')) {
                    const provider = fieldId.replace('api_key_', '').toUpperCase();
                    const apiKeyOverride = this.envStatus.overridden[`api_keys.${provider}`];
                    if (apiKeyOverride) {
                        return apiKeyOverride.env_var;
                    }
                }
                
                return null;
            },

            updateFilteredSections() {
                // Filter sections based on active tab - use section.tab instead of section.group
                if (this.activeTab === "agent") {
                    this.filteredSections =
                        this.settingsData.sections?.filter((section) => section.tab === "agent") || [];
                } else if (this.activeTab === "external") {
                    this.filteredSections =
                        this.settingsData.sections?.filter((section) => section.tab === "external") || [];
                } else if (this.activeTab === "mcp") {
                    this.filteredSections =
                        this.settingsData.sections?.filter((section) => section.tab === "mcp") || [];
                } else if (this.activeTab === "developer") {
                    this.filteredSections =
                        this.settingsData.sections?.filter((section) => section.tab === "developer") || [];
                } else {
                    // For any other tab (like scheduler), show nothing since those tabs have custom UI
                    this.filteredSections = [];
                }
            },

            async saveSettings() {
                // Initialize debounced function if not already done
                if (!this._debouncedSaveSettings) {
                    this.init();
                }
                
                // Show optimistic UI feedback
                this.isLoading = true;
                
                // Call the debounced version
                return this._debouncedSaveSettings();
            },

            async _actualSaveSettings() {
                try {
                    // First validate
                    for (const section of this.settingsData.sections) {
                        for (const field of section.fields) {
                            if (field.required && (!field.value || field.value.trim() === "")) {
                                showToast(`${field.title} in ${section.title} is required`, "error");
                                this.isLoading = false;
                                return;
                            }
                        }
                    }

                    // Prepare data
                    const formData = {};
                    for (const section of this.settingsData.sections) {
                        for (const field of section.fields) {
                            formData[field.id] = field.value;
                        }
                    }

                    // Send request
                    const response = await fetch("/settings_set", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(formData),
                    });

                    if (response.ok) {
                        showToast("Settings saved successfully", "success");
                        // Refresh settings
                        await this.fetchSettings();
                    } else {
                        const errorData = await response.json();
                        
                        // Handle validation errors from server (400 status)
                        if (response.status === 400 && errorData.validation_errors) {
                            const errorMessages = errorData.validation_errors.join('\n');
                            showToast(`Settings validation failed:\n${errorMessages}`, "error");
                        } else {
                            throw new Error(errorData.error || "Failed to save settings");
                        }
                    }
                } catch (error) {
                    logger.error("Error saving settings:", error);
                    showToast("Failed to save settings: " + error.message, "error");
                } finally {
                    this.isLoading = false;
                }
            },

            // Handle provider change for model filtering
            async handleProviderChange(providerId, newProvider) {
                try {
                    logger.info(`Provider changed to: ${newProvider}`);
                    
                    // Get the new models for this provider
                    const response = await fetch("/get_models_for_provider", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ provider: newProvider }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const models = data.models || [];
                        
                        // Add release date tooltips to model options
                        const enhancedModels = models.map(model => {
                            const enhanced = { ...model };
                            if (model.release_date) {
                                enhanced.tooltip = `Released: ${model.release_date}`;
                            }
                            return enhanced;
                        });
                        
                        // Find the corresponding model name field and update its options
                        const modelFieldId = providerId.replace('_provider', '_name');
                        for (const section of this.settingsData.sections) {
                            for (const field of section.fields) {
                                if (field.id === modelFieldId) {
                                    field.options = enhancedModels;
                                    // Reset the model value if current value is not in new options
                                    const currentValueExists = enhancedModels.some(model => model.value === field.value);
                                    if (!currentValueExists && enhancedModels.length > 0) {
                                        field.value = enhancedModels[0].value; // Set to first available model
                                        
                                        // Auto-update model parameters when model changes
                                        await this.handleModelChange(modelFieldId, field.value, newProvider);
                                    }
                                    break;
                                }
                            }
                        }
                    } else {
                        logger.error("Failed to fetch models for provider:", response.status);
                    }
                } catch (error) {
                    logger.error("Error handling provider change:", error);
                }
            },

            // Handle model change for automatic parameter updates
            async handleModelChange(modelFieldId, newModel, provider) {
                try {
                    logger.info(`Model changed: ${modelFieldId} to ${newModel} (provider: ${provider})`);
                    
                    // Get parameters for this model
                    const response = await fetch("/get_model_parameters", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ 
                            provider: provider, 
                            model_name: newModel 
                        }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const parameters = data.parameters || {};
                        
                        logger.debug(`Received parameters for ${newModel}:`, parameters);
                        
                        // Update related parameter fields
                        const baseId = modelFieldId.replace('_name', '');
                        
                        // Map of parameter keys to field suffixes
                        const parameterMapping = {
                            'ctx_length': '_ctx_length',
                            'vision': '_vision',
                            'rl_requests': '_rl_requests',
                            'rl_input': '_rl_input',
                            'rl_output': '_rl_output'
                        };
                        
                        for (const section of this.settingsData.sections) {
                            for (const field of section.fields) {
                                // Check if this field corresponds to a model parameter
                                for (const [paramKey, fieldSuffix] of Object.entries(parameterMapping)) {
                                    if (field.id === baseId + fieldSuffix && Object.prototype.hasOwnProperty.call(parameters, paramKey)) {
                                        const oldValue = field.value;
                                        field.value = parameters[paramKey];
                                        logger.debug(`Updated ${field.id}: ${oldValue} → ${field.value}`);
                                    }
                                }
                            }
                        }
                    } else {
                        logger.error("Failed to fetch model parameters:", response.status);
                    }
                } catch (error) {
                    logger.error("Error handling model change:", error);
                }
            },

            async refreshAllModels() {
                logger.info('Refreshing all model lists due to deprecated toggle change');
                
                // Find all provider selects
                const providerSelects = document.querySelectorAll('select[id$="_provider"]');
                
                for (const select of providerSelects) {
                    const providerId = select.id;
                    const currentProvider = select.value;
                    if (currentProvider) {
                        await this.handleProviderChange(providerId, currentProvider);
                    }
                }
            },

            // Handle special button field actions
            handleFieldButton(field) {
                if (field.action === "test_connection") {
                    this.testConnection(field);
                } else if (field.action === "reveal_token") {
                    this.revealToken(field);
                } else if (field.action === "generate_token") {
                    this.generateToken(field);
                } else {
                    logger.warn("Unknown button action:", field.action);
                }
            },

            // Test API connection
            async testConnection(field) {
                try {
                    field.testResult = "Testing...";
                    field.testStatus = "loading";

                    // Find the API key field
                    let apiKey = "";
                    for (const section of this.settingsData.sections) {
                        for (const f of section.fields) {
                            if (f.id === field.target) {
                                apiKey = f.value;
                                break;
                            }
                        }
                    }

                    if (!apiKey) {
                        throw new Error("API key is required");
                    }

                    // Send test request
                    const response = await fetch("/test_connection", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            service: field.service,
                            api_key: apiKey,
                        }),
                    });

                    const data = await response.json();

                    if (response.ok && data.success) {
                        field.testResult = "Connection successful!";
                        field.testStatus = "success";
                    } else {
                        throw new Error(data.error || "Connection failed");
                    }
                } catch (error) {
                    logger.error("Connection test failed:", error);
                    field.testResult = `Failed: ${error.message}`;
                    field.testStatus = "error";
                }
            },

            // Reveal token temporarily
            revealToken(field) {
                // Find target field
                for (const section of this.settingsData.sections) {
                    for (const f of section.fields) {
                        if (f.id === field.target) {
                            // Toggle field type
                            f.type = f.type === "password" ? "text" : "password";

                            // Update button text
                            field.value = f.type === "password" ? "Show" : "Hide";

                            break;
                        }
                    }
                }
            },

            // Generate random token
            generateToken(field) {
                // Find target field
                for (const section of this.settingsData.sections) {
                    for (const f of section.fields) {
                        if (f.id === field.target) {
                            // Generate random token
                            const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
                            let token = "";
                            for (let i = 0; i < 32; i++) {
                                token += chars.charAt(Math.floor(Math.random() * chars.length));
                            }

                            // Set field value
                            f.value = token;
                            break;
                        }
                    }
                }
            },

            closeModal() {
                // Stop scheduler polling before closing the modal
                const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                if (schedulerElement) {
                    const schedulerData = Alpine.$data(schedulerElement);
                    if (schedulerData && typeof schedulerData.stopPolling === "function") {
                        logger.info("Stopping scheduler polling on modal close");
                        schedulerData.stopPolling();
                    }
                }

                this.$store.root.isOpen = false;
            },
        }));
        logger.info("✅ Alpine settingsModal component registered via Component Manager");
    } else {
        // Fallback to direct registration if Component Manager not available
        try {
            Alpine.data("settingsModal", () => ({
                // ... existing implementation with minimal changes
                settingsData: {},
                filteredSections: [],
                activeTab: "agent",
                isLoading: true,
                // ... rest of the component implementation
            }));
            logger.info("✅ Alpine settingsModal component registered (fallback method)");
        } catch (error) {
            logger.error("❌ Error registering Alpine settingsModal component:", error);
        }
    }
});

// Show toast notification
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    // Remove after delay
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Make settingsModalProxy globally available for Alpine.js
window.settingsModalProxy = settingsModalProxy;
