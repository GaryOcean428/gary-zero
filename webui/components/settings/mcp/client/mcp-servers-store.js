// Import enhanced logger
import { logger } from './../../../../js/console-logger.js';

import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { scrollModal } from "/js/modals.js";
import sleep from "/js/sleep.js";

const model = {
    editor: null,
    servers: [],
    loading: true,
    statusCheck: false,
    serverLog: "",
    fallbackTextarea: null,
    hasUnsavedChanges: false,
    lastSavedContent: "",

    async initialize() {
        // Initialize the JSON Viewer after the modal is rendered
        const container = document.getElementById("mcp-servers-config-json");
        if (container) {
            try {
                const editor = ace.edit("mcp-servers-config-json");

                const dark = localStorage.getItem("darkMode");
                if (dark != "false") {
                    editor.setTheme("ace/theme/github_dark");
                } else {
                    editor.setTheme("ace/theme/tomorrow");
                }

                editor.session.setMode("ace/mode/json");
                
                // Safely get the JSON value
                let json = "";
                try {
                    const fieldConfig = this.getSettingsFieldConfigJson();
                    if (fieldConfig && fieldConfig.value) {
                        json = typeof fieldConfig.value === 'string' 
                            ? fieldConfig.value 
                            : JSON.stringify(fieldConfig.value, null, 2);
                    } else {
                        json = "{}"; // Default empty JSON object
                    }
                } catch (e) {
                    logger.warn("Failed to get initial JSON value:", e);
                    json = "{}";
                }
                
                // Safely set the value
                if (typeof json === 'string' && json.trim()) {
                    editor.setValue(json);
                } else {
                    editor.setValue("{}");
                }
                
                editor.clearSelection();
                this.editor = editor;
                this.lastSavedContent = editor.getValue();
                
                // Set up change tracking
                editor.on('change', () => {
                    this.hasUnsavedChanges = this.editor.getValue() !== this.lastSavedContent;
                    this.autoSave();
                });
                
            } catch (error) {
                logger.error("Failed to initialize Ace editor, using fallback:", error);
                this.initializeFallbackTextarea(container);
            }
        }

        this.startStatusCheck();
    },

    initializeFallbackTextarea(container) {
        // Create a fallback textarea if Ace editor fails
        const textarea = document.createElement('textarea');
        textarea.id = 'mcp-servers-config-fallback';
        textarea.style.width = '100%';
        textarea.style.height = '400px';
        textarea.style.fontFamily = 'monospace';
        textarea.style.fontSize = '14px';
        
        // Get initial value
        let json = "{}";
        try {
            const fieldConfig = this.getSettingsFieldConfigJson();
            if (fieldConfig && fieldConfig.value) {
                json = typeof fieldConfig.value === 'string' 
                    ? fieldConfig.value 
                    : JSON.stringify(fieldConfig.value, null, 2);
            }
        } catch (e) {
            logger.warn("Failed to get initial JSON value for fallback:", e);
        }
        
        textarea.value = json;
        this.lastSavedContent = json;
        
        // Replace the container content
        container.innerHTML = '';
        container.appendChild(textarea);
        
        this.fallbackTextarea = textarea;
        
        // Set up change tracking for fallback
        textarea.addEventListener('input', () => {
            this.hasUnsavedChanges = textarea.value !== this.lastSavedContent;
            this.autoSave();
        });
    },

    formatJson() {
        try {
            // get current content
            const currentContent = this.getEditorValue();

            // parse and format with 2 spaces indentation
            const parsed = JSON.parse(currentContent);
            const formatted = JSON.stringify(parsed, null, 2);

            // update editor content
            if (this.editor) {
                this.editor.setValue(formatted);
                this.editor.clearSelection();
                this.editor.navigateFileStart();
            } else if (this.fallbackTextarea) {
                this.fallbackTextarea.value = formatted;
            }
        } catch (error) {
            logger.error("Failed to format JSON:", error);
            alert("Invalid JSON: " + error.message);
        }
    },

    getEditorValue() {
        if (this.editor) {
            return this.editor.getValue();
        } else if (this.fallbackTextarea) {
            return this.fallbackTextarea.value;
        }
        return "{}";
    },

    getSettingsFieldConfigJson() {
        return settingsModalProxy.settings.sections
            .filter((x) => x.id == "mcp_client")[0]
            .fields.filter((x) => x.id == "mcp_servers")[0];
    },

    autoSave() {
        // Debounced auto-save to localStorage
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }
        
        this.autoSaveTimeout = setTimeout(() => {
            try {
                const content = this.getEditorValue();
                localStorage.setItem('mcp_servers_config_draft', content);
                logger.log('Auto-saved MCP servers config');
            } catch (e) {
                logger.error('Failed to auto-save:', e);
            }
        }, 1000);
    },

    onClose() {
        try {
            // Check for unsaved changes
            if (this.hasUnsavedChanges) {
                const confirmSave = confirm("You have unsaved changes. Do you want to save them?");
                if (confirmSave) {
                    const val = this.getEditorValue();
                    const fieldConfig = this.getSettingsFieldConfigJson();
                    if (fieldConfig) {
                        fieldConfig.value = val;
                    }
                }
            }
            
            // Clear auto-save draft
            localStorage.removeItem('mcp_servers_config_draft');
            
            // Stop status check
            this.stopStatusCheck();
        } catch (error) {
            logger.error("Error in onClose:", error);
        }
    },

    async startStatusCheck() {
        this.statusCheck = true;
        let firstLoad = true;

        while (this.statusCheck) {
            await this._statusCheck();
            if (firstLoad) {
                this.loading = false;
                firstLoad = false;
            }
            await sleep(3000);
        }
    },

    async _statusCheck() {
        const resp = await API.callJsonApi("mcp_servers_status", null);
        if (resp.success) {
            this.servers = resp.status;
            this.servers.sort((a, b) => a.name.localeCompare(b.name));
        }
    },

    async stopStatusCheck() {
        this.statusCheck = false;
    },

    async applyNow() {
        if (this.loading) return;
        this.loading = true;
        try {
            scrollModal("mcp-servers-status");
            const currentContent = this.getEditorValue();
            const resp = await API.callJsonApi("mcp_servers_apply", {
                mcp_servers: currentContent,
            });
            if (resp.success) {
                this.servers = resp.status;
                this.servers.sort((a, b) => a.name.localeCompare(b.name));
                this.lastSavedContent = currentContent;
                this.hasUnsavedChanges = false;
                // Clear auto-save draft after successful save
                localStorage.removeItem('mcp_servers_config_draft');
            }
            this.loading = false;
            await sleep(100); // wait for ui and scroll
            scrollModal("mcp-servers-status");
        } catch (error) {
            logger.error("Failed to apply MCP servers:", error);
            alert("Failed to apply MCP servers: " + error.message);
        }
        this.loading = false;
    },

    async getServerLog(serverName) {
        this.serverLog = "";
        const resp = await API.callJsonApi("mcp_server_get_log", {
            server_name: serverName,
        });
        if (resp.success) {
            this.serverLog = resp.log;
            openModal("settings/mcp/client/mcp-servers-log.html");
        }
    },

    async onToolCountClick(serverName) {
        const resp = await API.callJsonApi("mcp_server_get_detail", {
            server_name: serverName,
        });
        if (resp.success) {
            this.serverDetail = resp.detail;
            openModal("settings/mcp/client/mcp-server-tools.html");
        }
    },
};

const store = createStore("mcpServersStore", model);

export { store };