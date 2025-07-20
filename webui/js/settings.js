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
                console.warn("Root store not available during tab switch, will retry");
                // Retry after a short delay if store not ready
                setTimeout(() => {
                    const retryStore = Alpine.store("root");
                    if (retryStore) {
                        retryStore.activeTab = tabName;
                    }
                }, 100);
            }
        } catch (error) {
            console.warn("Error accessing Alpine store during tab switch:", error);
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
                console.log("Switching to scheduler tab, initializing Flatpickr");
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
                console.log("Switching to tunnel tab, initializing tunnelSettings");
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
        console.log("Settings modal opening");
        const modalEl = document.getElementById("settingsModal");
        if (!modalEl) {
            console.error("Settings modal element not found");
            return;
        }

        // Wait for Alpine to be ready and ensure component is initialized
        if (typeof Alpine === "undefined") {
            console.error("Alpine.js not available");
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
                    console.warn(`Attempt ${i + 1}: Error getting Alpine data:`, dataError.message);
                }
                // Wait progressively longer
                await new Promise((resolve) => setTimeout(resolve, 100 * (i + 1)));
            }

            if (!modalAD) {
                console.error("Settings modal not properly initialized with Alpine.js");
                return;
            }
        } catch (error) {
            console.error("Error accessing Alpine data:", error);
            return;
        }

        // First, ensure the store is updated properly with proper error handling
        let store = null;
        try {
            // Wait for Alpine to be fully ready
            if (typeof Alpine === 'undefined') {
                console.warn("Alpine.js not yet loaded, delaying settings modal open");
                setTimeout(() => this.openSettings(), 100);
                return new Promise((resolve) => { this.resolvePromise = resolve; });
            }
            
            store = Alpine.store("root");
            if (store) {
                // Set isOpen first to ensure proper state
                store.isOpen = true;
            } else {
                console.warn("Root store not found, will retry initialization");
                // Retry after Alpine is fully ready
                setTimeout(() => {
                    const retryStore = Alpine.store("root");
                    if (retryStore) {
                        retryStore.isOpen = true;
                    }
                }, 100);
            }
        } catch (error) {
            console.error("Error accessing Alpine store:", error);
        }

        //get settings from backend
        try {
            console.log("Fetching settings from /settings_get endpoint");
            const set = await sendJsonData("/settings_get", {});
            console.log("Settings fetch successful:", set);

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
                console.log(`Setting initial tab to: ${savedTab}`);

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
                    console.log(`Current active tab after direct set: ${modalAD.activeTab}`);
                    console.log(
                        "Scheduler tab active after direct initialization?",
                        schedulerTab && schedulerTab.classList.contains("active")
                    );

                    // Explicitly start polling if we're on the scheduler tab
                    if (modalAD.activeTab === "scheduler") {
                        console.log("Settings opened directly to scheduler tab, initializing polling");
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
                console.log("Stopping scheduler polling on modal close");
                schedulerData.stopPolling();
            }
        }
    },

    async handleFieldButton(field) {
        console.log(`Button clicked: ${field.id}`);

        if (field.id === "mcp_servers_config") {
            openModal("settings/mcp/client/mcp-servers.html");
        }
    },

    // Handle provider change for model filtering
    async handleProviderChange(providerId, newProvider) {
        try {
            console.log(`Provider changed: ${providerId} to ${newProvider}`);
            
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
                                    field.options = models;
                                    // Reset the model value if current value is not in new options
                                    const currentValueExists = models.some(model => model.value === field.value);
                                    if (!currentValueExists && models.length > 0) {
                                        field.value = models[0].value; // Set to first available model
                                    }
                                    console.log(`Updated ${modelFieldId} with ${models.length} models`);
                                    break;
                                }
                            }
                        }
                    }
                }
            } else {
                console.error("Failed to fetch models for provider:", response.status);
            }
        } catch (error) {
            console.error("Error handling provider change:", error);
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
    
    // Initialize settings modal Alpine component
    try {
        Alpine.data("settingsModal", () => ({
            settingsData: {},
            filteredSections: [],
            activeTab: "agent",
            isLoading: true,

            async init() {
                try {
                    // Wait for root store to be available with retry logic
                    let rootStore = null;
                    let retryCount = 0;
                    const maxRetries = 10;
                    
                    while (!rootStore && retryCount < maxRetries) {
                        try {
                            rootStore = Alpine.store("root");
                            if (rootStore) break;
                        } catch (error) {
                            console.warn(`Retry ${retryCount + 1}: Root store not ready yet`);
                        }
                        await new Promise(resolve => setTimeout(resolve, 50));
                        retryCount++;
                    }
                    
                    if (rootStore) {
                        this.activeTab = rootStore.activeTab || "agent";
                    } else {
                        console.warn("Root store not available after retries, using default");
                        this.activeTab = "agent";
                    }
                    if (rootStore) {
                        this.activeTab = rootStore.activeTab || "agent";
                    } else {
                        console.warn("Root store not available after retries, using default");
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

                    // Load settings
                    await this.fetchSettings();
                    this.updateFilteredSections();
                } catch (error) {
                    console.error("Error in settingsModal init:", error);
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
                            console.warn("Root store not available during tab switch, will retry");
                            // Retry after a short delay if store not ready
                            setTimeout(() => {
                                const retryStore = Alpine.store("root");
                                if (retryStore) {
                                    retryStore.activeTab = tab;
                                }
                            }, 100);
                        }
                    } catch (error) {
                        console.warn("Error accessing Alpine store during tab switch:", error);
                    }

                    // Save to localStorage
                    localStorage.setItem("settingsActiveTab", tab);

                    // Update filtered sections
                    this.updateFilteredSections();
                } catch (error) {
                    console.error("Error switching tab:", error);
                }
            },

            async fetchSettings() {
                try {
                    this.isLoading = true;
                    console.log("Fetching settings from /settings_get endpoint");
                    const response = await fetch("/settings_get", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({}),
                    });

                    console.log("Settings response status:", response.status, response.statusText);
                    if (response.ok) {
                        const data = await response.json();
                        console.log("Settings data received:", data);
                        if (data && data.settings) {
                            this.settingsData = data.settings;
                        } else {
                            console.error("Invalid settings data format:", data);
                        }
                    } else {
                        const errorText = await response.text();
                        console.error("Failed to fetch settings:", response.status, response.statusText, errorText);
                    }
                } catch (error) {
                    console.error("Error fetching settings:", error);
                } finally {
                    this.isLoading = false;
                }
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
                try {
                    // First validate
                    for (const section of this.settingsData.sections) {
                        for (const field of section.fields) {
                            if (field.required && (!field.value || field.value.trim() === "")) {
                                showToast(`${field.title} in ${section.title} is required`, "error");
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
                        throw new Error(errorData.error || "Failed to save settings");
                    }
                } catch (error) {
                    console.error("Error saving settings:", error);
                    showToast("Failed to save settings: " + error.message, "error");
                }
            },

            // Handle provider change for model filtering
            async handleProviderChange(providerId, newProvider) {
                try {
                    console.log(`Provider changed to: ${newProvider}`);
                    
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
                        
                        // Find the corresponding model name field and update its options
                        const modelFieldId = providerId.replace('_provider', '_name');
                        for (const section of this.settingsData.sections) {
                            for (const field of section.fields) {
                                if (field.id === modelFieldId) {
                                    field.options = models;
                                    // Reset the model value if current value is not in new options
                                    const currentValueExists = models.some(model => model.value === field.value);
                                    if (!currentValueExists && models.length > 0) {
                                        field.value = models[0].value; // Set to first available model
                                    }
                                    break;
                                }
                            }
                        }
                    } else {
                        console.error("Failed to fetch models for provider:", response.status);
                    }
                } catch (error) {
                    console.error("Error handling provider change:", error);
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
                    console.warn("Unknown button action:", field.action);
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
                    console.error("Connection test failed:", error);
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
                        console.log("Stopping scheduler polling on modal close");
                        schedulerData.stopPolling();
                    }
                }

                this.$store.root.isOpen = false;
            },
        }));
        console.log("✅ Alpine settingsModal component registered successfully");
    } catch (error) {
        console.error("❌ Error registering Alpine settingsModal component:", error);
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
