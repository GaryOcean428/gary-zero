import * as msgs from "./js/messages.js";
import { speech } from "./js/speech.js";

// --- Global State ---
let autoScroll = true;
let context = "";
let connectionStatus = false;
let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;
let appInitialized = false;

// Message containers for tracking
const messageContainers = new Map();

// --- Global UI Element Variables ---
let leftPanel, rightPanel, chatInput, sendButton, chatHistory;
let inputSection, statusSection, chatsSection, tasksSection, progressBar, autoScrollSwitch;
let sidebarOverlay, toggleSidebarButton;

// --- Utility and Helper Functions ---

function setMessage(id, type, heading, content, temp, kvps) {
    if (!chatHistory) {
        console.warn('Chat history element not found, unable to set message');
        return;
    }

    // Check if message already exists
    let messageContainer = messageContainers.get(id);
    if (messageContainer) {
        // Update existing message
        messageContainer.innerHTML = '';
    } else {
        // Create new message container
        messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container');
        messageContainer.setAttribute('data-message-id', id);
        chatHistory.appendChild(messageContainer);
        messageContainers.set(id, messageContainer);
    }

    // Get the appropriate message handler
    const handler = msgs.getHandler(type);
    if (handler) {
        handler(messageContainer, id, type, heading, content, temp, kvps);
    } else {
        console.warn(`No handler found for message type: ${type}`);
        msgs.drawMessageDefault(messageContainer, id, type, heading, content, temp, kvps);
    }

    // Auto-scroll if enabled
    if (autoScroll && chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

function generateGUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function adjustTextareaHeight() {
    if (!chatInput) return;
    chatInput.style.height = 'auto';
    chatInput.style.height = `${chatInput.scrollHeight}px`;
}

function isMobile() {
    return window.innerWidth <= 768;
}

function toggleCssProperty(selector, property, value) {
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
}

// --- Toast Notifications ---

function hideToast() {
    const toastEl = document.getElementById('toast');
    if (!toastEl) return;
    if (toastEl.timeoutId) clearTimeout(toastEl.timeoutId);
    toastEl.classList.remove('show');
    setTimeout(() => { toastEl.style.display = 'none'; }, 400);
}

function toast(text, type = 'info', timeout = 5000) {
    const toastEl = document.getElementById('toast');
    if (!toastEl) return;
    if (toastEl.timeoutId) clearTimeout(toastEl.timeoutId);

    toastEl.querySelector('.toast__title').textContent = type.charAt(0).toUpperCase() + type.slice(1);
    toastEl.querySelector('.toast__message').textContent = text;
    toastEl.className = `toast toast--${type}`;
    
    const copyButton = toastEl.querySelector('.toast__copy');
    copyButton.style.display = type === 'error' ? 'inline-block' : 'none';
    copyButton.onclick = () => {
        navigator.clipboard.writeText(text);
        copyButton.textContent = 'Copied!';
        setTimeout(() => { copyButton.textContent = 'Copy'; }, 2000);
    };

    toastEl.querySelector('.toast__close').onclick = hideToast;
    
    toastEl.style.display = 'flex';
    setTimeout(() => toastEl.classList.add('show'), 10);

    if (timeout) {
        toastEl.timeoutId = setTimeout(hideToast, Math.max(timeout, 5000));
    }
}
window.toast = toast;


function toastFetchError(text, error) {
    const message = connectionStatus ? `${text}: ${error.message}` : `${text} (backend disconnected): ${error.message}`;
    toast(message, "error");
    console.error(text, error);
}
window.toastFetchError = toastFetchError;

// --- Backend Communication ---

async function sendJsonData(url, data) {
    let retries = 3;
    let lastError = null;
    
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                // Handle 502 gateway errors specifically
                if (response.status === 502) {
                    lastError = new Error(`Server temporarily unavailable (${response.status})`);
                    if (i < retries - 1) {
                        // Wait longer between retries for 502 errors
                        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
                        continue;
                    }
                } else {
                    throw new Error(errorText);
                }
            } else {
                return await response.json();
            }
        } catch (error) {
            lastError = error;
            if (i < retries - 1) {
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 500 * (i + 1)));
                continue;
            }
        }
    }
    
    // If we get here, all retries failed
    throw lastError;
}
window.sendJsonData = sendJsonData;

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
            const alternateChat = chatsAD.contexts?.find(ctx => ctx.id !== id);
            if (alternateChat) {
                setContext(alternateChat.id);
                return;
            }
        }
        
        if (window.Alpine && tasksSection?.__x?.$data) {
            const tasksAD = Alpine.$data(tasksSection);
            const alternateTask = tasksAD.tasks?.find(task => task.id !== id);
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
        const statusIcon = statusSection.querySelector('.status-icon');
        if (statusIcon) {
            const connectedCircle = statusIcon.querySelector('.connected-circle');
            const disconnectedCircle = statusIcon.querySelector('.disconnected-circle');
            if (connectedCircle && disconnectedCircle) {
                connectedCircle.style.opacity = connected ? '1' : '0';
                disconnectedCircle.style.opacity = connected ? '0' : '1';
            }
        }
    }
}

// --- UI Interaction Functions ---

function toggleSidebar(show) {
    if (!leftPanel || !rightPanel || !sidebarOverlay) return;
    const showSidebar = typeof show === 'boolean' ? show : leftPanel.classList.contains('hidden');
    leftPanel.classList.toggle('hidden', !showSidebar);
    rightPanel.classList.toggle('expanded', !showSidebar);
    sidebarOverlay.classList.toggle('visible', showSidebar && isMobile());
}

function handleResize() {
    if (!leftPanel || !rightPanel || !sidebarOverlay) return;
    if (isMobile()) {
        leftPanel.classList.add('hidden');
        rightPanel.classList.remove('expanded');
        sidebarOverlay.classList.remove('visible');
    } else {
        leftPanel.classList.remove('hidden');
        rightPanel.classList.add('expanded');
        sidebarOverlay.classList.remove('visible');
    }
}

function updateAfterScroll() {
    if (!chatHistory) return;
    const tolerancePx = 50;
    const isAtBottom = (chatHistory.scrollHeight - chatHistory.scrollTop) <= (chatHistory.clientHeight + tolerancePx);
    if (autoScrollSwitch) {
        autoScrollSwitch.checked = isAtBottom;
        autoScroll = isAtBottom;
    }
}

function handleChatInputKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// --- Main Application Logic ---

async function poll() {
    try {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const response = await sendJsonData("/poll", {
            log_from: lastLogVersion,
            context: context || null,
            timezone: timezone
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
            lastLogVersion = 0;
            lastLogGuid = response.log_guid;
        }

        if (lastLogVersion !== response.log_version) {
            response.logs.forEach(log => {
                setMessage(log.id || log.no, log.type, log.heading, log.content, log.temp, log.kvps);
            });
            afterMessagesUpdate(response.logs);
            lastLogVersion = response.log_version;
            updateProgress(response.log_progress, response.log_progress_active);
            return true;
        }
    } catch (error) {
        console.error('Error in polling function:', error);
        setConnectionStatus(false);
    }
    return false;
}

async function startPolling() {
    const shortInterval = 25;
    const longInterval = 250;
    const shortIntervalPeriod = 100;
    let shortIntervalCount = 0;

    async function _doPoll() {
        try {
            const updated = await poll();
            if (updated) shortIntervalCount = shortIntervalPeriod;
            
            const nextInterval = shortIntervalCount > 0 ? shortInterval : longInterval;
            if(shortIntervalCount > 0) shortIntervalCount--;

            setTimeout(_doPoll, nextInterval);
        } catch (error) {
            console.error('Error in polling loop:', error);
            
            // Use longer interval when errors occur
            const errorInterval = Math.min(longInterval * 4, 2000); // Max 2 seconds
            setTimeout(_doPoll, errorInterval);
        }
    }
    _doPoll();
}

function afterMessagesUpdate(logs) {
    if (localStorage.getItem('speech') === 'true') {
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
        'right-panel',
        'chat-history',
        'chat-input',
        'send-button',
        'status-section',
        'progress-bar',
        'auto-scroll-switch',
        'left-panel'
    ];
    console.log('🔍 UI visibility check');
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (!el) {
            console.warn(`❌ #${id} missing`);
            return;
        }
        const style = window.getComputedStyle(el);
        const visible =
            style.display !== 'none' &&
            style.visibility !== 'hidden' &&
            parseFloat(style.opacity) !== 0 &&
            el.offsetParent !== null;
        console.log(`${visible ? '✅' : '⚠️'} #${id}`);
        if (!visible) {
            el.style.display = '';
            el.style.visibility = 'visible';
            el.style.opacity = '1';
        }
    });
}
window.verifyUIVisibility = verifyUIVisibility;

// --- Global Window Functions for UI interaction ---

function newChat() {
    try {
        setContext(generateGUID());
        updateAfterScroll();
    } catch (e) {
        toastFetchError("Error creating new chat", e);
    }
};
window.newChat = newChat;

async function sendMessage() {
    if (!chatInput || !inputSection) return;

    try {
        const message = chatInput.value.trim();
        const inputAD = Alpine.$data(inputSection);
        const attachments = inputAD.attachments;
        const hasAttachments = attachments && attachments.length > 0;

        if (message || hasAttachments) {
            const messageId = generateGUID();
            let response;

            if (hasAttachments) {
                const attachmentsWithUrls = attachments.map(att => ({ ...att, url: URL.createObjectURL(att.file) }));
                setMessage(messageId, 'user', '', message, false, { attachments: attachmentsWithUrls });

                const formData = new FormData();
                formData.append('text', message);
                formData.append('context', context);
                formData.append('message_id', messageId);
                attachments.forEach(att => formData.append('attachments', att.file));

                response = await fetch('/message_async', { method: 'POST', body: formData });
            } else {
                setMessage(messageId, 'user', '', message, false);
                const data = { text: message, context, message_id: messageId };
                response = await fetch('/message_async', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }

            const jsonResponse = await response.json();
            if (jsonResponse && jsonResponse.context) {
                setContext(jsonResponse.context);
            } else {
                toast("No response context returned.", "error");
            }

            chatInput.value = '';
            inputAD.attachments = [];
            inputAD.hasAttachments = false;
            adjustTextareaHeight();
        }
    } catch (e) {
        toastFetchError("Error sending message", e);
    }
}
window.sendMessage = sendMessage;

async function pauseAgent(paused) {
    try {
        await sendJsonData("/pause", { paused, context });
    } catch (e) {
        toastFetchError("Error pausing agent", e);
    }
}
window.pauseAgent = pauseAgent;

async function resetChat(ctxid = null) {
    try {
        await sendJsonData("/chat_reset", { "context": ctxid || context });
        if (!ctxid) updateAfterScroll();
    } catch (e) {
        toastFetchError("Error resetting chat", e);
    }
}
window.resetChat = resetChat;

async function killChat(id) {
    if (!id) return console.error("No chat ID provided for deletion");
    try {
        const chatsAD = Alpine.$data(chatsSection);
        if (context === id) {
            const alternateChat = chatsAD.contexts.find(ctx => ctx.id !== id);
            setContext(alternateChat ? alternateChat.id : generateGUID());
        }
        await sendJsonData("/chat_remove", { context: id });
        chatsAD.contexts = chatsAD.contexts.filter(ctx => ctx.id !== id);
        updateAfterScroll();
        toast("Chat deleted successfully", "success");
    } catch (e) {
        toastFetchError("Error deleting chat", e);
    }
}
window.killChat = killChat;

async function selectChat(id) {
    if (id === context) return;

    const activeTab = localStorage.getItem('activeTab') || 'chats';
    const tasksAD = Alpine.$data(tasksSection);
    const isTask = tasksAD?.tasks?.some(task => task.id === id);

    if (isTask && activeTab !== 'tasks') {
        return activateTab('tasks', id);
    }
    if (!isTask && activeTab !== 'chats') {
        return activateTab('chats', id);
    }

    setContext(id);
    localStorage.setItem(isTask ? 'lastSelectedTask' : 'lastSelectedChat', id);
    poll();
    updateAfterScroll();
}
window.selectChat = selectChat;

function toggleDarkMode(isDark) {
    document.body.classList.toggle('dark-mode', isDark);
    document.body.classList.toggle('light-mode', !isDark);
    localStorage.setItem('darkMode', isDark);
};
window.toggleDarkMode = toggleDarkMode;

function toggleAutoScroll(shouldAutoScroll) {
    autoScroll = shouldAutoScroll;
    localStorage.setItem('autoScroll', shouldAutoScroll);
    if (autoScrollSwitch) autoScrollSwitch.checked = shouldAutoScroll;
};
window.toggleAutoScroll = toggleAutoScroll;

window.toggleJson = (show) => toggleCssProperty('.msg-json', 'display', show ? 'block' : 'none');
window.toggleThoughts = (show) => toggleCssProperty('.msg-thoughts', 'display', show ? 'block' : 'none');
window.toggleUtils = (show) => toggleCssProperty('.message-util', 'display', show ? 'block' : 'none');

window.toggleSpeech = function (isOn) {
    localStorage.setItem('speech', isOn);
    if (!isOn) speech.stop();
};

window.nudge = async () => {
    try {
        await sendJsonData("/nudge", { ctxid: getContext() });
    } catch (e) {
        toastFetchError("Error nudging agent", e);
    }
}

window.restart = async () => {
    if (!connectionStatus) return toast("Backend disconnected, cannot restart.", "error");
    try {
        await sendJsonData("/restart", {});
    } catch {
        toast("Restarting...", "info", 0);
        for (let i = 0; i < 240; i++) {
            try {
                await sendJsonData("/health", {});
                hideToast();
                await new Promise(r => setTimeout(r, 400));
                return toast("Restarted", "success", 5000);
            } catch {
                await new Promise(r => setTimeout(r, 250));
            }
        }
        hideToast();
        await new Promise(r => setTimeout(r, 400));
        toast("Restart timed out or failed", "error", 5000);
    }
}

async function readJsonFiles() {
    return new Promise((resolve, reject) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.multiple = true;
        input.onchange = async () => {
            if (!input.files.length) return resolve([]);
            const readPromises = Array.from(input.files).map(file => 
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
            toast("No response or chats returned.", "error");
        }
    } catch (e) {
        toastFetchError("Error loading chats", e);
    }
}

window.saveChat = async () => {
    try {
        const response = await sendJsonData("/chat_export", { ctxid: context });
        if (response) {
            downloadFile(`${response.ctxid}.json`, response.content);
            toast("Chat file downloaded.", "success");
        } else {
            toast("No response returned.", "error");
        }
    } catch (e) {
        toastFetchError("Error saving chat", e);
    }
}

function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

function setupTabs() {
    const chatsTab = document.getElementById('chats-tab');
    const tasksTab = document.getElementById('tasks-tab');
    if (chatsTab && tasksTab) {
        chatsTab.addEventListener('click', () => activateTab('chats'));
        tasksTab.addEventListener('click', () => activateTab('tasks'));
    } else {
        setTimeout(setupTabs, 100);
    }
}

function activateTab(tabName, contextId = null) {
    const chatsTab = document.getElementById('chats-tab');
    const tasksTab = document.getElementById('tasks-tab');
    const chatsSection = document.getElementById('chats-section');
    const tasksSection = document.getElementById('tasks-section');

    if (!chatsTab || !tasksTab || !chatsSection || !tasksSection) return;

    const previousTab = localStorage.getItem('activeTab');
    if (previousTab === 'chats') {
        localStorage.setItem('lastSelectedChat', context);
    } else if (previousTab === 'tasks') {
        localStorage.setItem('lastSelectedTask', context);
    }

    localStorage.setItem('activeTab', tabName);
    chatsTab.classList.toggle('active', tabName === 'chats');
    tasksTab.classList.toggle('active', tabName === 'tasks');
    chatsSection.style.display = tabName === 'chats' ? '' : 'none';
    tasksSection.style.display = tabName === 'tasks' ? 'flex' : 'none';
    if (tabName === 'tasks') {
        tasksSection.style.flexDirection = 'column';
    }

    const newContextId = contextId || localStorage.getItem(tabName === 'chats' ? 'lastSelectedChat' : 'lastSelectedTask');
    if (newContextId && newContextId !== context) {
        setContext(newContextId);
    }
    poll();
}

function initializeActiveTab() {
    if (!localStorage.getItem('lastSelectedChat')) localStorage.setItem('lastSelectedChat', '');
    if (!localStorage.getItem('lastSelectedTask')) localStorage.setItem('lastSelectedTask', '');
    const activeTab = localStorage.getItem('activeTab') || 'chats';
    activateTab(activeTab);
}

function openTaskDetail(taskId) {
    if (window.Alpine) {
        const settingsButton = document.getElementById('settings');
        if (settingsButton) {
            settingsButton.click();
            const modalEl = document.getElementById('settingsModal');
            if (!modalEl) return console.error('Settings modal element not found');
            const modalData = Alpine.$data(modalEl);
            setTimeout(() => {
                modalData.switchTab('scheduler');
                setTimeout(() => {
                    const schedulerComponent = document.querySelector('[x-data="schedulerSettings"]');
                    if (!schedulerComponent) return console.error('Scheduler component not found');
                    Alpine.$data(schedulerComponent).showTaskDetail(taskId);
                }, 50);
            }, 25);
        } else {
            console.error('Settings button not found');
        }
    } else {
        console.error('Alpine.js not loaded');
    }
}
window.openTaskDetail = openTaskDetail;

function handleFiles(files, inputAD) {
    Array.from(files).forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        const isImage = ['jpg', 'jpeg', 'png', 'bmp'].includes(ext);
        const attachment = { file, type: isImage ? 'image' : 'file', name: file.name, extension: ext };

        if (isImage) {
            const reader = new FileReader();
            reader.onload = e => {
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
}

window.handleFileUpload = function(event) {
    handleFiles(event.target.files, Alpine.$data(inputSection));
}

window.loadKnowledge = async function () {
    try {
        const fileContents = await readJsonFiles();
        const response = await sendJsonData("/import_knowledge", { knowledge: fileContents });
        toast(response ? "Knowledge imported." : "No response returned.", response ? "success" : "error");
    } catch (e) {
        toastFetchError("Error importing knowledge", e);
    }
}

// --- App Initialization ---

function setupEventListeners() {
    // Chat input event listeners
    if (chatInput) {
        chatInput.addEventListener('keydown', handleChatInputKeydown);
        chatInput.addEventListener('input', adjustTextareaHeight);
    }

    // Send button event listener
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    // Auto-scroll switch event listener
    if (autoScrollSwitch) {
        autoScrollSwitch.addEventListener('change', (e) => {
            toggleAutoScroll(e.target.checked);
        });
    }

    // Chat history scroll event listener
    if (chatHistory) {
        chatHistory.addEventListener('scroll', updateAfterScroll);
    }

    // Sidebar toggle event listeners
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', () => toggleSidebar());
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => toggleSidebar(false));
    }

    // Window resize event listener
    window.addEventListener('resize', handleResize);

    console.log('✅ Event listeners set up successfully.');
}

function initializeApp() {
    if (appInitialized) return;
    appInitialized = true;

    console.log('🚀 Starting application initialization...');

    // Wait for DOM elements to be available with retry mechanism
    function waitForElements(attempt = 1) {
        const selectors = {
            leftPanel: '#left-panel', rightPanel: '#right-panel',
            chatInput: '#chat-input', sendButton: '#send-button', chatHistory: '#chat-history',
            inputSection: '#input-section', statusSection: '#status-section', chatsSection: '#chats-section',
            tasksSection: '#tasks-section', progressBar: '#progress-bar', autoScrollSwitch: '#auto-scroll-switch',
            sidebarOverlay: '#sidebar-overlay', toggleSidebarButton: '#toggle-sidebar',
        };

        const missing = [];
        Object.entries(selectors).forEach(([key, selector]) => {
            const element = document.querySelector(selector);
            // Assign to global variables
            switch(key) {
                case 'leftPanel': leftPanel = element; break;
                case 'rightPanel': rightPanel = element; break;
                case 'chatInput': chatInput = element; break;
                case 'sendButton': sendButton = element; break;
                case 'chatHistory': chatHistory = element; break;
                case 'inputSection': inputSection = element; break;
                case 'statusSection': statusSection = element; break;
                case 'chatsSection': chatsSection = element; break;
                case 'tasksSection': tasksSection = element; break;
                case 'progressBar': progressBar = element; break;
                case 'autoScrollSwitch': autoScrollSwitch = element; break;
                case 'sidebarOverlay': sidebarOverlay = element; break;
                case 'toggleSidebarButton': toggleSidebarButton = element; break;
            }
            if (!element) {
                missing.push({ key, selector });
            }
        });

        if (missing.length > 0 && attempt < 5) {
            console.log(`⏳ Attempt ${attempt}: ${missing.length} elements not yet available, retrying...`);
            setTimeout(() => waitForElements(attempt + 1), 100);
            return;
        }

        if (missing.length > 0) {
            console.warn('⚠️ Some elements still not found after retries:', missing.map(m => m.key).join(', '));
        } else {
            console.log('✅ All DOM elements found successfully');
        }

        continueInitialization();
    }

    function continueInitialization() {
        setupEventListeners();
        setupTabs();
        initializeActiveTab();
        handleResize();

        toggleDarkMode(localStorage.getItem('darkMode') !== 'false');
        if (autoScrollSwitch) {
            const savedAutoScroll = localStorage.getItem('autoScroll') !== 'false';
            autoScrollSwitch.checked = savedAutoScroll;
            toggleAutoScroll(savedAutoScroll);
        }

        startPolling();
        verifyUIVisibility();
        console.log('✅ Application initialization complete.');
    }

    // Start the element waiting process
    waitForElements();
}

document.addEventListener('DOMContentLoaded', () => {
    // This is a good place for any setup that must happen after the initial DOM is parsed,
    // but before Alpine or other scripts might be ready.
});

document.addEventListener('alpine:initialized', () => {
    console.log('Alpine.js initialized. Running app initialization.');
    initializeApp();
});

// Fallback for cases where the script loads after Alpine is already initialized
if (window.Alpine && window.Alpine.version) {
    setTimeout(() => {
        if (!appInitialized) {
            console.log('Alpine.js was already initialized. Running app initialization.');
            initializeApp();
        }
    }, 0);
}
