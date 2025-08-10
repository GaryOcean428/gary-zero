import * as msgs from "./js/messages.js";
import { speech } from "./js/speech.js";

// --- App Boot Management ---
if (window.__APP_BOOTED__) { 
    console.debug('App already booted, skipping init'); 
    // Don't continue with initialization if already booted
} else {
    // Continue with normal initialization
    window.__APP_BOOTED__ = true;
    
    // Queue early fetchCurrentModel calls until boot completes
    const earlyCalls = [];
    window.fetchCurrentModel = (...args) => earlyCalls.push(args);
    
    // Store the early calls queue globally so we can process them later
    window.__earlyFetchCurrentModelCalls = earlyCalls;
}

// --- Global State ---
let autoScroll = true; // Used by toggleAutoScroll and setMessage functions
let context = null;
let connectionStatus = false;
let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;

// Message containers for tracking
const messageContainers = new Map();

// Track locally created user messages to prevent duplicates from server polling
const localUserMessages = new Set();

// --- Global UI Element Variables ---
let leftPanel, rightPanel, chatInput, chatHistory;
let inputSection, statusSection, chatsSection, tasksSection, progressBar, autoScrollSwitch;
let sidebarOverlay;

// --- Utility and Helper Functions ---

function setMessage(id, type, heading, content, temp, kvps) {
    if (!chatHistory) {
        // console.warn('Chat history element not found, unable to set message');
        return;
    }

    // Skip user messages that were already created locally to prevent duplicates
    if (type === "user" && localUserMessages.has(id)) {
        console.log(`🚫 Skipping duplicate user message from server: ${id}`);
        return;
    }

    // Check if message already exists
    let messageContainer = messageContainers.get(id);
    if (messageContainer) {
        // Update existing message
        console.log(`🔄 Updating existing message: ${id} (${type})`);
        messageContainer.innerHTML = "";
    } else {
        // Create new message container
        console.log(`✨ Creating new message: ${id} (${type})`);
        messageContainer = document.createElement("div");
        messageContainer.classList.add("message-container");
        messageContainer.setAttribute("data-message-id", id);
        chatHistory.appendChild(messageContainer);
        messageContainers.set(id, messageContainer);
    }

    // Check for potential duplicates in DOM (additional safety check)
    const existingMessages = chatHistory.querySelectorAll(`[data-message-id="${id}"]`);
    if (existingMessages.length > 1) {
        console.warn(`⚠️ Duplicate message containers detected for ID: ${id}`, existingMessages);
        // Remove duplicates, keeping only the first one
        for (let i = 1; i < existingMessages.length; i++) {
            existingMessages[i].remove();
        }
    }

    // Get the appropriate message handler
    const handler = msgs.getHandler(type);
    if (handler) {
        handler(messageContainer, id, type, heading, content, temp, kvps);
    } else {
        // console.warn(`No handler found for message type: ${type}`);
        msgs.drawMessageDefault(messageContainer, id, type, heading, content, temp, kvps);
    }

    // Auto-scroll if enabled
    if (autoScroll && chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

function generateGUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

function adjustTextareaHeight() {
    if (!chatInput) return;
    chatInput.style.height = "auto";
    chatInput.style.height = `${chatInput.scrollHeight}px`;
}

function isMobile() {
    return window.innerWidth <= 768;
}

function toggleCssProperty(selector, property, value) {
    // First try the existing stylesheet approach for backward compatibility
    for (const sheet of document.styleSheets) {
        try {
            for (const rule of sheet.cssRules || sheet.rules) {
                if (rule.selectorText === selector) {
                    if (value === undefined) {
                        rule.style.removeProperty(property);
                    } else {
                        rule.style.setProperty(property, value);
                    }
                    return;
                }
            }
            // Ignore CORS errors for cross-origin stylesheets
        } catch {
            // Intentionally empty - ignoring CORS errors
        }
    }
    
    // Fallback: Create or update a dynamic style element
    const dynamicStyleId = 'dynamic-toggle-styles';
    let dynamicStyle = document.getElementById(dynamicStyleId);
    
    if (!dynamicStyle) {
        dynamicStyle = document.createElement('style');
        dynamicStyle.id = dynamicStyleId;
        dynamicStyle.type = 'text/css';
        document.head.appendChild(dynamicStyle);
    }
    
    // Track current rules in the dynamic style element
    if (!window._dynamicToggleRules) {
        window._dynamicToggleRules = new Map();
    }
    
    const ruleKey = `${selector}:${property}`;
    
    if (value === undefined) {
        // Remove the rule
        window._dynamicToggleRules.delete(ruleKey);
    } else {
        // Add or update the rule
        window._dynamicToggleRules.set(ruleKey, `${selector} { ${property}: ${value} !important; }`);
    }
    
    // Rebuild the dynamic stylesheet
    const allRules = Array.from(window._dynamicToggleRules.values()).join('\n');
    dynamicStyle.textContent = allRules;
}

// --- Toast Notifications ---

function hideToast() {
    const toastEl = document.getElementById("toast");
    if (!toastEl) return;
    if (toastEl.timeoutId) clearTimeout(toastEl.timeoutId);
    toastEl.classList.remove("show");
    setTimeout(() => {
        toastEl.style.display = "none";
    }, 400);
}

function toast(text, type = "info", timeout = 5000) {
    const toastEl = document.getElementById("toast");
    if (!toastEl) return;
    if (toastEl.timeoutId) clearTimeout(toastEl.timeoutId);

    toastEl.querySelector(".toast__title").textContent = type.charAt(0).toUpperCase() + type.slice(1);
    toastEl.querySelector(".toast__message").textContent = text;
    toastEl.className = `toast toast--${type}`;

    const copyButton = toastEl.querySelector(".toast__copy");
    copyButton.style.display = type === "error" ? "inline-block" : "none";
    copyButton.onclick = () => {
        navigator.clipboard.writeText(text);
        copyButton.textContent = "Copied!";
        setTimeout(() => {
            copyButton.textContent = "Copy";
        }, 2000);
    };

    toastEl.querySelector(".toast__close").onclick = hideToast;

    toastEl.style.display = "flex";
    setTimeout(() => toastEl.classList.add("show"), 10);

    if (timeout) {
        toastEl.timeoutId = setTimeout(hideToast, Math.max(timeout, 5000));
    }
}
window.toast = toast;

function toastFetchError(text, error) {
    toast(`${text}: ${error.message || error}`, "error");
}
window.toastFetchError = toastFetchError;

// --- Backend Communication ---

async function sendJsonData(url, data) {
    const retries = 3;
    let lastError = null;
    
    // Only log requests for non-polling endpoints to reduce console noise
    if (url !== "/poll") {
        console.log(`📡 Sending request to ${url}`, data);
    }

    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });

            // Only log responses for non-polling endpoints to reduce console noise
            if (url !== "/poll") {
                console.log(`📡 Response from ${url}: ${response.status} ${response.statusText}`);
            }

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ Request failed for ${url}:`, {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorText
                });
                // Handle 502 gateway errors specifically
                if (response.status === 502) {
                    lastError = new Error(`Server temporarily unavailable (${response.status})`);
                    if (i < retries - 1) {
                        console.log(`🔄 Retrying ${url} in ${1000 * (i + 1)}ms due to 502 error`);
                        // Wait longer between retries for 502 errors
                        await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
                    }
                } else {
                    throw new Error(`${response.status}: ${errorText}`);
                }
            } else {
                const result = await response.json();
                // Only log success for non-polling endpoints to reduce console noise
                if (url !== "/poll") {
                    console.log(`✅ Success from ${url}:`, result);
                }
                return result;
            }
        } catch (error) {
            console.error(`❌ Network error for ${url} (attempt ${i + 1}):`, error);
            lastError = error;
            if (i < retries - 1) {
                console.log(`🔄 Retrying ${url} in ${500 * (i + 1)}ms due to network error`);
                // Wait before retry
                await new Promise((resolve) => setTimeout(resolve, 500 * (i + 1)));
            }
        }
    }

    // If we get here, all retries failed
    console.error(`💥 All retries failed for ${url}:`, lastError);
    throw lastError;
}
window.sendJsonData = sendJsonData;

// --- Model Management Functions ---

async function fetchCurrentModel() {
    try {
        const response = await sendJsonData("/get_current_model", {});
        if (response && !response.error) {
            // Update the model indicator
            const indicator = document.getElementById("model-indicator");
            if (indicator) {
                const modelData = {
                    model_label: response.model_label || response.model_name || "Unknown",
                    display_name: response.display_name || "Unknown Model",
                    capabilities: response.capabilities || []
                };
                
                // Update Alpine.js data if available
                if (typeof Alpine !== 'undefined') {
                    const alpineData = Alpine.$data(indicator);
                    if (alpineData) {
                        alpineData.currentModel = modelData;
                    }
                }
                
                // Fallback: direct DOM update
                indicator.textContent = modelData.model_label;
                indicator.title = `Current model: ${modelData.display_name}`;
                
                // Add capability indicators as CSS classes
                indicator.className = 'model-indicator';
                if (modelData.capabilities.includes('voice')) {
                    indicator.classList.add('model-voice');
                }
                if (modelData.capabilities.includes('code')) {
                    indicator.classList.add('model-code');
                }
                if (modelData.capabilities.includes('vision')) {
                    indicator.classList.add('model-vision');
                }
                
                console.log('✅ Updated model indicator:', modelData);
            }
        } else {
            console.error('❌ Error fetching current model:', response?.error || 'Unknown error');
        }
    } catch (error) {
        console.error('❌ Failed to fetch current model:', error);
    }
}

window.fetchCurrentModel = fetchCurrentModel;

// Process any early calls that were queued during initialization
if (window.__earlyFetchCurrentModelCalls && window.__earlyFetchCurrentModelCalls.length > 0) {
    console.debug('Processing', window.__earlyFetchCurrentModelCalls.length, 'queued fetchCurrentModel calls');
    const earlyCallsToProcess = [...window.__earlyFetchCurrentModelCalls];
    window.__earlyFetchCurrentModelCalls.length = 0; // Clear the queue
    
    // Process queued calls
    earlyCallsToProcess.forEach(args => {
        try {
            fetchCurrentModel(...args);
        } catch (error) {
            console.warn('Error processing queued fetchCurrentModel call:', error);
        }
    });
}

// --- State Management ---

function setContext(id) {
    if (id === context) return;
    context = id;
    lastLogGuid = "";
    lastLogVersion = 0;
    lastSpokenNo = 0;
    if (chatHistory) chatHistory.innerHTML = "";

    if (chatsSection?.__x?.$data) chatsSection.__x.$data.selected = id;
    if (tasksSection?.__x?.$data) tasksSection.__x.$data.selected = id;
}
window.setContext = setContext;

function getContext() {
    return context;
}
window.getContext = getContext;

function switchFromContext(id) {
    // If the current context matches the id being removed, switch to an alternative
    if (context === id) {
        // Try to find an alternative context from available chats or tasks
        if (window.Alpine && chatsSection?.__x?.$data) {
            const chatsAD = Alpine.$data(chatsSection);
            const alternateChat = chatsAD.contexts?.find((ctx) => ctx.id !== id);
            if (alternateChat) {
                setContext(alternateChat.id);
                return;
            }
        }

        if (window.Alpine && tasksSection?.__x?.$data) {
            const tasksAD = Alpine.$data(tasksSection);
            const alternateTask = tasksAD.tasks?.find((task) => task.id !== id);
            if (alternateTask) {
                setContext(alternateTask.id);
                return;
            }
        }

        // If no alternative found, create a new context
        setContext(generateGUID());
    }
}

// Export for module imports
export { getContext, switchFromContext };

function setConnectionStatus(connected) {
    connectionStatus = connected;
    if (statusSection) {
        const statusIcon = statusSection.querySelector(".status-icon");
        if (statusIcon) {
            const connectedCircle = statusIcon.querySelector(".connected-circle");
            const disconnectedCircle = statusIcon.querySelector(".disconnected-circle");
            if (connectedCircle && disconnectedCircle) {
                connectedCircle.style.opacity = connected ? "1" : "0";
                disconnectedCircle.style.opacity = connected ? "0" : "1";
            }
        }
    }
}

// --- UI Interaction Functions ---

function updateAfterScroll() {
    if (!chatHistory) return;
    const tolerancePx = 50;
    const isAtBottom = chatHistory.scrollHeight - chatHistory.scrollTop <= chatHistory.clientHeight + tolerancePx;
    if (autoScrollSwitch) {
        autoScrollSwitch.checked = isAtBottom;
        autoScroll = isAtBottom;
    }
}

// --- Main Application Logic ---

async function poll() {
    try {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const response = await sendJsonData("/poll", {
            log_from: lastLogVersion,
            context: context || null,
            timezone: timezone,
        });

        if (!response) {
            setConnectionStatus(false);
            return false;
        }

        setConnectionStatus(true);

        if (!context && response.context) setContext(response.context);
        if (response.context !== context) return false;

        if (lastLogGuid !== response.log_guid) {
            if (chatHistory) chatHistory.innerHTML = "";
            // Clear local user messages tracking when chat history is cleared
            localUserMessages.clear();
            lastLogVersion = 0;
            lastLogGuid = response.log_guid;
        }

        if (lastLogVersion !== response.log_version) {
            response.logs.forEach((log) => {
                setMessage(log.id || log.no, log.type, log.heading, log.content, log.temp, log.kvps);
            });
            afterMessagesUpdate(response.logs);
            lastLogVersion = response.log_version;
            updateProgress(response.log_progress, response.log_progress_active);
            return true;
        }
    } catch (error) {
        console.error("Network error during polling:", error);
        setConnectionStatus(false);
        toastFetchError("Network error during polling", error);
    }
    return false;
}

function afterMessagesUpdate(logs) {
    if (localStorage.getItem("speech") === "true") {
        speakMessages(logs);
    }
}

function speakMessages(logs) {
    for (let i = logs.length - 1; i >= 0; i--) {
        const log = logs[i];
        if (log.type === "response" && log.no > lastSpokenNo) {
            lastSpokenNo = log.no;
            speech.speak(log.content);
            return;
        }
    }
}

function updateProgress(progress, active) {
    if (!progressBar) return;
    progress = progress || "";
    progressBar.classList.toggle("shiny-text", active);
    if (progressBar.innerHTML !== progress) {
        progressBar.innerHTML = progress;
    }
}

function verifyUIVisibility() {
    const elements = [
        "right-panel",
        "chat-history",
        "chat-input",
        "send-button",
        "status-section",
        "progress-bar",
        "auto-scroll-switch",
        "left-panel",
    ];
    // console.log('🔍 UI visibility check');
    elements.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) {
            // console.warn(`❌ #${id} missing`);
            return;
        }
        const style = window.getComputedStyle(el);
        const visible =
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            parseFloat(style.opacity) !== 0 &&
            el.offsetParent !== null;
        // console.log(`${visible ? '✅' : '⚠️'} #${id}`);
        if (!visible) {
            el.style.display = "";
            el.style.visibility = "visible";
            el.style.opacity = "1";
        }
    });
}
window.verifyUIVisibility = verifyUIVisibility;

// --- Global Window Functions for UI interaction ---

function newChat() {
    try {
        setContext(generateGUID());
        // Clear local user messages tracking for new chat
        localUserMessages.clear();
        updateAfterScroll();
    } catch (error) {
        console.error("Error creating new chat:", error);
        toastFetchError("Error creating new chat", error);
    }
}
window.newChat = newChat;

async function sendMessage() {
    if (!chatInput || !inputSection) return;

    try {
        const message = chatInput.value.trim();
        const inputAD = window.Alpine && inputSection?.__x?.$data ? Alpine.$data(inputSection) : null;
        const attachments = inputAD?.attachments || [];
        const hasAttachments = attachments && attachments.length > 0;

        if (message || hasAttachments) {
            const messageId = generateGUID();
            const clientMessageId = generateGUID(); // Generate unique client message ID for idempotency
            let response;

            if (hasAttachments) {
                const attachmentsWithUrls = attachments.map((att) => ({
                    ...att,
                    url: URL.createObjectURL(att.file),
                }));
                setMessage(messageId, "user", "", message, false, {
                    attachments: attachmentsWithUrls,
                });
                // Track this as a locally created user message
                localUserMessages.add(messageId);

                const formData = new FormData();
                formData.append("text", message);
                formData.append("context", context);
                formData.append("message_id", messageId);
                formData.append("client_message_id", clientMessageId);
                attachments.forEach((att) => formData.append("attachments", att.file));

                response = await fetch("/message_async", {
                    method: "POST",
                    body: formData,
                });
            } else {
                setMessage(messageId, "user", "", message, false);
                // Track this as a locally created user message
                localUserMessages.add(messageId);
                const data = { text: message, context, message_id: messageId, client_message_id: clientMessageId };
                response = await fetch("/message_async", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "Idempotency-Key": clientMessageId // Also send as header
                    },
                    body: JSON.stringify(data),
                });
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const jsonResponse = await response.json();
            
            // Check if this was a duplicate message
            if (jsonResponse && jsonResponse.duplicate) {
                console.log(`🚫 Message was duplicate, skipping: ${clientMessageId}`);
                return;
            }
            
            if (jsonResponse && jsonResponse.context) {
                setContext(jsonResponse.context);
            } else {
                console.warn("No response context returned from /message_async");
                toast("No response context returned.", "warning");
            }

            chatInput.value = "";
            if (inputAD) {
                inputAD.attachments = [];
                inputAD.hasAttachments = false;
            }
            adjustTextareaHeight();
        }
    } catch (error) {
        console.error("Error sending message:", error);
        toastFetchError("Error sending message", error);
    }
}
window.sendMessage = sendMessage;

async function pauseAgent(paused) {
    try {
        await sendJsonData("/pause", { paused, context });
    } catch (error) {
        console.error("Failed to pause agent:", error);
        toast("Failed to pause agent", "error");
    }
}
window.pauseAgent = pauseAgent;

async function resetChat(ctxid = null) {
    try {
        await sendJsonData("/chat_reset", { context: ctxid || context });
        if (!ctxid) updateAfterScroll();
    } catch (error) {
        console.error("Failed to reset chat:", error);
        toast("Failed to reset chat", "error");
    }
}
window.resetChat = resetChat;

async function killChat(id) {
    if (!id) return;
    try {
        const chatsAD = Alpine.$data(chatsSection);
        if (context === id) {
            const alternateChat = chatsAD.contexts.find((ctx) => ctx.id !== id);
            setContext(alternateChat ? alternateChat.id : generateGUID());
        }
        await sendJsonData("/chat_remove", { context: id });
        if (chatsAD?.contexts?.length > 0) {
            chatsAD.contexts = chatsAD.contexts.filter((ctx) => ctx.id !== id);
        }
        updateAfterScroll();
        toast("Chat deleted successfully", "success");
    } catch (error) {
        toastFetchError("Error deleting chat", error);
    }
}
window.killChat = killChat;

async function selectChat(id) {
    if (id === context) return;

    const activeTab = localStorage.getItem("activeTab") || "chats";
    const tasksAD = Alpine.$data(tasksSection);
    const isTask = tasksAD?.tasks?.some((task) => task.id === id);

    if (isTask && activeTab !== "tasks") {
        return activateTab("tasks", id);
    }
    if (!isTask && activeTab !== "chats") {
        return activateTab("chats", id);
    }

    setContext(id);
    localStorage.setItem(isTask ? "lastSelectedTask" : "lastSelectedChat", id);
    poll();
    updateAfterScroll();
}
window.selectChat = selectChat;

function toggleDarkMode(isDark) {
    document.body.classList.toggle("dark-mode", isDark);
    document.body.classList.toggle("light-mode", !isDark);
    localStorage.setItem("darkMode", isDark);
}
window.toggleDarkMode = toggleDarkMode;

function toggleAutoScroll(shouldAutoScroll) {
    autoScroll = shouldAutoScroll;
    localStorage.setItem("autoScroll", shouldAutoScroll);
    if (autoScrollSwitch) autoScrollSwitch.checked = shouldAutoScroll;
}
window.toggleAutoScroll = toggleAutoScroll;

window.toggleJson = (show) => toggleCssProperty(".msg-json", "display", show ? "block" : "none");
window.toggleThoughts = (show) => toggleCssProperty(".msg-thoughts", "display", show ? "block" : "none");
window.toggleUtils = (show) => {
    // Toggle both utility messages and agent messages together
    toggleCssProperty(".message-util", "display", show ? "block" : "none");
    toggleCssProperty(".message-agent:not(.message-user)", "display", show ? "block" : "none");
};

// Add specific agent message visibility toggle
window.toggleAgents = (show) => toggleCssProperty(".message-agent:not(.message-user)", "display", show ? "block" : "none");

window.toggleSpeech = (isOn) => {
    localStorage.setItem("speech", isOn);
    if (!isOn) speech.stop();
};

window.nudge = async () => {
    try {
        await sendJsonData("/nudge", { ctxid: getContext() });
    } catch (error) {
        toastFetchError("Error nudging agent", error);
    }
};

window.restart = async () => {
    if (!connectionStatus) return toast("Backend disconnected, cannot restart.", "error");
    try {
        await sendJsonData("/restart", {});
    } catch (error) {
        // This is expected to fail as the server shuts down. We can ignore it.
        // eslint-disable-next-line no-console
        console.log("Restart initiated, server shutting down:", error.message);
    }

    toast("Restarting...", "info", 0);
    for (let i = 0; i < 240; i++) {
        try {
            await new Promise((r) => setTimeout(r, 250)); // wait before check
            await sendJsonData("/health", {});
            hideToast();
            await new Promise((r) => setTimeout(r, 400));
            return toast("Restarted", "success", 5000);
        } catch (error) {
            // Not ready yet, continue loop
            // eslint-disable-next-line no-console
            console.log("Health check failed, retrying...", error.message);
        }
    }
    hideToast();
    await new Promise((r) => setTimeout(r, 400));
    toast("Restart timed out or failed", "error", 5000);
};

async function readJsonFiles() {
    return new Promise((resolve, reject) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".json";
        input.multiple = true;
        input.onchange = async () => {
            if (!input.files.length) return resolve([]);
            const readPromises = Array.from(input.files).map(
                (file) =>
                    new Promise((res, rej) => {
                        const reader = new FileReader();
                        reader.onload = () => res(reader.result);
                        reader.onerror = rej;
                        reader.readAsText(file);
                    })
            );
            try {
                resolve(await Promise.all(readPromises));
            } catch (error) {
                reject(error);
            }
        };
        input.click();
    });
}

window.loadChats = async () => {
    try {
        const fileContents = await readJsonFiles();
        const response = await sendJsonData("/chat_load", { chats: fileContents });
        if (response?.ctxids?.length) {
            setContext(response.ctxids[0]);
            toast("Chats loaded.", "success");
        } else {
            console.warn("No chats returned from server");
            toast("No chats could be loaded from the selected files.", "warning");
        }
    } catch (error) {
        console.error("Error loading chats:", error);
        toastFetchError("Error loading chats", error);
    }
};

async function saveChat() {
    try {
        const response = await sendJsonData("/chat_export", { ctxid: context });
        if (response) {
            downloadFile(`${response.ctxid}.json`, response.content);
            toast("Chat file downloaded.", "success");
        } else {
            console.warn("No response returned from /chat_export");
            toast("No response returned from server.", "error");
        }
    } catch (error) {
        console.error("Error saving chat:", error);
        toastFetchError("Error saving chat", error);
    }
}
window.saveChat = saveChat;

function downloadFile(filename, content) {
    const blob = new Blob([content], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

function activateTab(tabName, contextId = null) {
    const chatsTab = document.getElementById("chats-tab");
    const tasksTab = document.getElementById("tasks-tab");
    const chatsSection = document.getElementById("chats-section");
    const tasksSection = document.getElementById("tasks-section");

    if (!chatsTab || !tasksTab || !chatsSection || !tasksSection) return;

    const previousTab = localStorage.getItem("activeTab");
    if (previousTab === "chats") {
        localStorage.setItem("lastSelectedChat", context);
    } else if (previousTab === "tasks") {
        localStorage.setItem("lastSelectedTask", context);
    }

    localStorage.setItem("activeTab", tabName);
    chatsTab.classList.toggle("active", tabName === "chats");
    tasksTab.classList.toggle("active", tabName === "tasks");
    chatsSection.style.display = tabName === "chats" ? "" : "none";
    tasksSection.style.display = tabName === "tasks" ? "flex" : "none";
    if (tabName === "tasks") {
        tasksSection.style.flexDirection = "column";
    }

    const newContextId =
        contextId || localStorage.getItem(tabName === "chats" ? "lastSelectedChat" : "lastSelectedTask");
    if (newContextId && newContextId !== context) {
        setContext(newContextId);
    }
    poll();
}

function openTaskDetail(taskId) {
    if (window.Alpine) {
        const settingsButton = document.getElementById("settings");
        if (settingsButton) {
            setTimeout(() => {
                const element = document.getElementById(`task-detail-${taskId}`);
                if (element) {
                    element.scrollIntoView({ behavior: "smooth", block: "center" });
                    element.classList.add("highlight");
                    setTimeout(() => element.classList.remove("highlight"), 3000);
                }
            }, 100);
        } else {
            // Settings button not found
        }
    } else {
        // Alpine.js not loaded
    }
}
window.openTaskDetail = openTaskDetail;

window.handleFileUpload = (event) => {
    const element = document.getElementById("input-attachments-display");
    const inputAD = window.Alpine && element?.__x?.$data ? Alpine.$data(element) : null;
    if (!inputAD) return;

    Array.from(event.target.files).forEach((file) => {
        const ext = file.name.split(".").pop().toLowerCase();
        const isImage = ["jpg", "jpeg", "png", "bmp"].includes(ext);
        const attachment = {
            file,
            type: isImage ? "image" : "file",
            name: file.name,
            extension: ext,
        };

        if (isImage) {
            const reader = new FileReader();
            reader.onload = (e) => {
                attachment.url = e.target.result;
                inputAD.attachments.push(attachment);
                inputAD.hasAttachments = true;
            };
            reader.readAsDataURL(file);
        } else {
            inputAD.attachments.push(attachment);
            inputAD.hasAttachments = true;
        }
    });
};

window.loadKnowledge = async () => {
    try {
        const response = await fetch("/load_knowledge", { method: "POST" });
        const data = await response.json();
        if (data.success) {
            toast("Knowledge base loaded.", "success");
        } else {
            toast("Failed to load knowledge base.", "error");
        }
    } catch (error) {
        toastFetchError("Error loading knowledge base", error);
    }
};

// --- App Initialization ---

function initializeApp() {
    // Check if already initialized to prevent multiple runs
    if (window._appInitialized) {
        return;
    }
    window._appInitialized = true;

    const darkMode = localStorage.getItem("darkMode") !== "false";
    const savedAutoScroll = localStorage.getItem("autoScroll") !== "false"; // Default to true

    function setupEventListeners() {
        // Chat input event listeners
        if (chatInput) {
            chatInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            chatInput.addEventListener("input", adjustTextareaHeight);
        }

        // Send button event listener
        const sendButtonElem = document.getElementById("send-button");
        if (sendButtonElem) {
            sendButtonElem.addEventListener("click", sendMessage);
        }

        // Auto-scroll switch event listener
        if (autoScrollSwitch) {
            autoScrollSwitch.addEventListener("change", (e) => {
                toggleAutoScroll(e.target.checked);
            });
        }

        // Chat history scroll event listener
        if (chatHistory) {
            chatHistory.addEventListener("scroll", updateAfterScroll);
        }

        // Sidebar toggle event listeners
        const toggleSidebarButtonElem = document.getElementById("toggle-sidebar");
        if (toggleSidebarButtonElem) {
            toggleSidebarButtonElem.addEventListener("click", () => {
                if (!leftPanel || !sidebarOverlay) return;

                const isHidden = leftPanel.classList.contains("hidden");

                if (isHidden) {
                    leftPanel.classList.remove("hidden");
                    if (isMobile()) {
                        sidebarOverlay.classList.add("visible");
                    }
                } else {
                    leftPanel.classList.add("hidden");
                    sidebarOverlay.classList.remove("visible");
                }
            });
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener("click", () => {
                if (!leftPanel) return;
                leftPanel.classList.add("hidden");
                sidebarOverlay.classList.remove("visible");
            });
        }

        // Window resize event listener
        window.addEventListener("resize", () => {
            handleWindowResize();
        });
    }

    function handleWindowResize() {
        if (!leftPanel || !rightPanel || !sidebarOverlay) return;

        if (isMobile()) {
            leftPanel.classList.add("hidden");
            rightPanel.classList.remove("expanded");
            sidebarOverlay.classList.remove("visible");
        } else {
            leftPanel.classList.remove("hidden");
            rightPanel.classList.add("expanded");
            sidebarOverlay.classList.remove("visible");
        }
    }

    function waitForElements(attempt = 1) {
        const selectors = {
            leftPanel: "#left-panel",
            rightPanel: "#right-panel",
            chatInput: "#chat-input",
            chatHistory: "#chat-history",
            inputSection: "#input-section",
            statusSection: "#status-section",
            chatsSection: "#chats-section",
            tasksSection: "#tasks-section",
            progressBar: "#progress-bar",
            autoScrollSwitch: "#auto-scroll-switch",
            sidebarOverlay: "#sidebar-overlay",
        };

        const missing = [];
        const found = [];

        Object.entries(selectors).forEach(([key, selector]) => {
            const element = document.querySelector(selector);

            // Assign to global variables
            switch (key) {
                case "leftPanel":
                    leftPanel = element;
                    break;
                case "rightPanel":
                    rightPanel = element;
                    break;
                case "chatInput":
                    chatInput = element;
                    break;
                case "chatHistory":
                    chatHistory = element;
                    break;
                case "inputSection":
                    inputSection = element;
                    break;
                case "statusSection":
                    statusSection = element;
                    break;
                case "chatsSection":
                    chatsSection = element;
                    break;
                case "tasksSection":
                    tasksSection = element;
                    break;
                case "progressBar":
                    progressBar = element;
                    break;
                case "autoScrollSwitch":
                    autoScrollSwitch = element;
                    break;
                case "sidebarOverlay":
                    sidebarOverlay = element;
                    break;
            }

            if (element) {
                found.push(key);
            } else {
                missing.push({ key, selector });
            }
        });

        // Continue if we have the essential elements or max attempts reached
        const essentialElements = ["rightPanel", "chatInput", "chatHistory"];
        const hasEssentials = essentialElements.every((key) => found.includes(key));

        if (hasEssentials || attempt >= 10) {
            continueInitialization();
        } else {
            setTimeout(() => waitForElements(attempt + 1), 200);
        }
    }

    function continueInitialization() {
        // Ensure critical elements are visible
        ensureElementsVisible();

        setupEventListeners();
        setupTabs();
        setupInitialState();
        setupPolling();
    }

    function ensureElementsVisible() {
        // Try to rebuild missing UI elements first
        if (window.UIStructureRebuilder) {
            const rebuilder = new window.UIStructureRebuilder();
            const result = rebuilder.rebuildMissingElements();
            if (result.success && result.rebuilt.length > 0) {
                // Re-query elements after rebuilding
                setTimeout(() => {
                    waitForElements(1);
                }, 100);
                return;
            }
            rebuilder.ensureVisibility();
        }

        const criticalElements = [
            { id: "right-panel", name: "Right Panel" },
            { id: "chat-history", name: "Chat History" },
            { id: "chat-input", name: "Chat Input" },
            { id: "send-button", name: "Send Button" },
            { id: "input-section", name: "Input Section" },
        ];

        criticalElements.forEach(({ id }) => {
            const element = document.getElementById(id);
            if (element) {
                // Force visibility
                element.style.display = "";
                element.style.visibility = "visible";
                element.style.opacity = "1";
            }
        });

        // Force right panel to be expanded by default
        if (rightPanel) {
            rightPanel.classList.add("expanded");
        }
    }

    function setupTabs() {
        const chatsTab = document.getElementById("chats-tab");
        const tasksTab = document.getElementById("tasks-tab");

        if (chatsTab && tasksTab) {
            chatsTab.addEventListener("click", () => activateTab("chats"));
            tasksTab.addEventListener("click", () => activateTab("tasks"));
        } else {
            setTimeout(() => {
                const cTab = document.getElementById("chats-tab");
                const tTab = document.getElementById("tasks-tab");
                if (cTab) cTab.addEventListener("click", () => activateTab("chats"));
                if (tTab) tTab.addEventListener("click", () => activateTab("tasks"));
            }, 200);
        }
    }

    function setupInitialState() {
        // Initialize localStorage defaults
        if (!localStorage.getItem("lastSelectedChat")) {
            localStorage.setItem("lastSelectedChat", "");
        }
        if (!localStorage.getItem("lastSelectedTask")) {
            localStorage.setItem("lastSelectedTask", "");
        }

        // Activate initial tab
        const activeTab = localStorage.getItem("activeTab") || "chats";
        activateTab(activeTab);

        // Handle responsive layout
        handleWindowResize();

        // Apply theme
        toggleDarkMode(darkMode);

        // Set up auto-scroll
        if (autoScrollSwitch) {
            autoScrollSwitch.checked = savedAutoScroll;
            toggleAutoScroll(savedAutoScroll);
        }
        
        // Initialize toggle states for thoughts and utilities
        const showThoughts = localStorage.getItem("showThoughts") !== "false"; // Default to true
        const showUtils = localStorage.getItem("showUtils") === "true"; // Default to false
        const showAgents = localStorage.getItem("showAgents") !== "false"; // Default to true
        const showJson = localStorage.getItem("showJson") === "true"; // Default to false
        
        // Apply the toggle states
        if (window.toggleThoughts) window.toggleThoughts(showThoughts);
        if (window.toggleUtils) window.toggleUtils(showUtils);
        if (window.toggleAgents) window.toggleAgents(showAgents);
        if (window.toggleJson) window.toggleJson(showJson);
    }

    function setupPolling() {
        (async () => {
            const shortInterval = 100;
            const longInterval = 500;
            const shortIntervalPeriod = 50;
            let shortIntervalCount = 0;
            let consecutiveErrors = 0;

            async function _doPoll() {
                try {
                    const updated = await poll();

                    if (updated) {
                        shortIntervalCount = shortIntervalPeriod;
                        consecutiveErrors = 0; // Reset error count on success
                    }

                    const nextInterval = shortIntervalCount > 0 ? shortInterval : longInterval;
                    if (shortIntervalCount > 0) shortIntervalCount--;

                    setTimeout(_doPoll, nextInterval);
                } catch (error) {
                    consecutiveErrors++;
                    console.error(`Polling error (attempt ${consecutiveErrors}):`, error);

                    // Use progressively longer intervals on consecutive errors
                    const errorInterval = Math.min(longInterval * 2 ** Math.min(consecutiveErrors - 1, 4), 10000);
                    
                    // Show error to user after multiple consecutive failures
                    if (consecutiveErrors >= 5) {
                        console.warn(`Polling has failed ${consecutiveErrors} times consecutively`);
                        if (consecutiveErrors === 5) {
                            toast("Connection issues detected. Retrying...", "warning", 3000);
                        }
                    }
                    
                    setTimeout(_doPoll, errorInterval);
                }
            }

            // Start polling immediately
            _doPoll();
        })();

        // Final UI verification
        setTimeout(() => {
            verifyUIVisibility();
            
            // Fetch current model information for the indicator
            fetchCurrentModel();
            
            // Listen for settings updates to refresh model info
            document.addEventListener('settings-updated', () => {
                console.log('🔄 Settings updated, refreshing model indicator');
                setTimeout(fetchCurrentModel, 500); // Small delay to ensure settings are saved
            });
        }, 1000);
    }

    // Start the initialization process
    waitForElements();
}

document.addEventListener("DOMContentLoaded", () => {
    // This is a good place for any setup that must happen after the initial DOM is parsed,
    // but before Alpine or other scripts might be ready.
});

document.addEventListener("alpine:initialized", () => {
    initializeApp();
});

// Fallback for cases where the script loads after Alpine is already initialized
if (window.Alpine?.version) {
    setTimeout(() => {
        const appInitialized = false;
        if (!appInitialized) {
            initializeApp();
        }
    }, 0);
}
