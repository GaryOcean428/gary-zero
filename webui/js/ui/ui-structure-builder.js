export class UIStructureBuilder {
  static buildCompleteInterface() {
    console.log('🎨 Building complete chat interface...');
    let appContainer = document.getElementById('app');
    if (!appContainer) {
      appContainer = document.createElement('div');
      appContainer.id = 'app';
      document.body.appendChild(appContainer);
    }

    // Clear any previous UI to avoid duplicate fragments
    while (appContainer.firstChild) {
      appContainer.removeChild(appContainer.firstChild);
    }

    const template = `
      <div class="app-layout">
        <div id="right-panel" class="chat-container">
          <div class="chat-header">
            <div class="header-content">
              <h2>Agent Chat</h2>
              <div class="header-actions">
                <button class="icon-button" title="Clear chat">
                  <i class="icon-trash"></i>
                </button>
              </div>
            </div>
          </div>
          <div id="chat-history" class="chat-history">
            <div class="messages-container"></div>
          </div>
          <div id="input-section" class="input-section">
            <div class="input-container">
              <div class="input-wrapper">
                <textarea id="chat-input" class="chat-input" placeholder="Type your message here..." rows="1"></textarea>
                <div class="input-actions">
                  <button id="send-button" class="send-button" title="Send message">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
                    </svg>
                  </button>
                  <button class="voice-button" title="Voice input">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 15c1.66 0 2.99-1.34 2.99-3L15 6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3z"></path>
                      <path d="M17.3 12c0 3-2.54 5.1-5.3 5.1S6.7 15 6.7 12H5c0 3.42 2.72 6.23 6 6.72V22h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div id="status-section" class="status-bar">
          <div class="status-content">
            <div id="progress-bar" class="progress-bar">
              <div class="progress-fill"></div>
            </div>
            <div class="status-info">
              <span class="status-text">Ready</span>
              <label class="auto-scroll-toggle">
                <input type="checkbox" id="auto-scroll-switch" checked>
                <span>Auto-scroll</span>
              </label>
            </div>
          </div>
        </div>
      </div>`;

    const fragment = document.createRange().createContextualFragment(template);
    appContainer.appendChild(fragment);
    this.injectCompleteStyles();
    this.initializeMessageHandlers();
    console.log('✅ Complete UI structure built');
  }

  static injectCompleteStyles() {
    if (document.getElementById('complete-ui-styles')) return;
    const styles = document.createElement('style');
    styles.id = 'complete-ui-styles';
    styles.textContent = `
      * { box-sizing: border-box; }
      .app-layout { display: flex; flex-direction: column; height: 100vh; background: #1a1a1a; }
      .chat-container { flex: 1; display: flex; flex-direction: column; background: #0d0d0d; position: relative; overflow: hidden; }
      .chat-header { background: #1a1a1a; border-bottom: 1px solid #333; padding: 1rem 1.5rem; }
      .header-content { display: flex; justify-content: space-between; align-items: center; }
      .chat-header h2 { margin: 0; color: #fff; font-size: 1.25rem; font-weight: 500; }
      .chat-history { flex: 1; overflow-y: auto; padding: 1.5rem; background: #0d0d0d; }
      .messages-container { max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem; }
      .message { display: flex; gap: 1rem; animation: fadeIn 0.3s ease-out; }
      .message.user { justify-content: flex-end; }
      .message-content { max-width: 70%; padding: 1rem 1.5rem; border-radius: 12px; position: relative; }
      .message.user .message-content { background: #4a5568; color: #fff; border-bottom-right-radius: 4px; }
      .message.agent .message-content { background: #2d3748; color: #fff; border-bottom-left-radius: 4px; }
      .message-header { font-size: 0.875rem; color: #718096; margin-bottom: 0.5rem; font-weight: 500; }
      .message.agent .message-header { color: #63b3ed; }
      .input-section { background: #1a1a1a; border-top: 1px solid #333; padding: 1rem 1.5rem; }
      .input-container { max-width: 900px; margin: 0 auto; }
      .input-wrapper { display: flex; align-items: flex-end; gap: 0.75rem; background: #2d2d2d; border-radius: 24px; padding: 0.5rem; border: 1px solid #404040; transition: border-color 0.2s; }
      .input-wrapper:focus-within { border-color: #4299e1; }
      .chat-input { flex: 1; background: transparent; border: none; color: #fff; padding: 0.5rem 1rem; font-size: 1rem; resize: none; outline: none; max-height: 120px; line-height: 1.5; }
      .chat-input::placeholder { color: #666; }
      .input-actions { display: flex; gap: 0.5rem; }
      .send-button, .voice-button { width: 36px; height: 36px; border-radius: 50%; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
      .send-button { background: #4299e1; color: white; }
      .send-button:hover { background: #3182ce; transform: scale(1.05); }
      .voice-button { background: transparent; color: #666; }
      .voice-button:hover { background: #333; color: #fff; }
      .status-bar { background: #1a1a1a; border-top: 1px solid #333; padding: 0.5rem 1.5rem; }
      .status-content { display: flex; align-items: center; gap: 1rem; max-width: 900px; margin: 0 auto; }
      .progress-bar { flex: 1; height: 3px; background: #333; border-radius: 2px; overflow: hidden; }
      .progress-fill { height: 100%; background: #4299e1; width: 0%; transition: width 0.3s ease; }
      .status-info { display: flex; align-items: center; gap: 1rem; }
      .status-text { color: #666; font-size: 0.875rem; }
      .auto-scroll-toggle { display: flex; align-items: center; gap: 0.5rem; color: #666; font-size: 0.875rem; cursor: pointer; }
      .auto-scroll-toggle input { cursor: pointer; }
      @keyframes fadeIn { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
      .chat-history::-webkit-scrollbar { width: 8px; }
      .chat-history::-webkit-scrollbar-track { background:#1a1a1a; }
      .chat-history::-webkit-scrollbar-thumb { background:#333; border-radius:4px; }
      .chat-history::-webkit-scrollbar-thumb:hover { background:#444; }
      .icon-button { background:transparent; border:none; color:#666; cursor:pointer; padding:0.5rem; border-radius:6px; transition:all 0.2s; }
      .icon-button:hover { background:#333; color:#fff; }
    `;
    document.head.appendChild(styles);
  }

  static initializeMessageHandlers() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;
      });
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          document.getElementById('send-button')?.click();
        }
      });
    }
    window.renderMessage = function (type, content, metadata = {}) {
      const messagesContainer = document.querySelector('.messages-container');
      if (!messagesContainer) return;
      const messageEl = document.createElement('div');
      messageEl.className = `message ${type}`;
      if (type === 'agent') {
        messageEl.innerHTML = `
          <div class="message-content">
            <div class="message-header">Agent ${metadata.agentId || '0'}: ${metadata.status || 'Responding'}</div>
            <div class="message-body">${content}</div>
          </div>`;
      } else {
        messageEl.innerHTML = `
          <div class="message-content">
            <div class="message-header">User</div>
            <div class="message-body">${content}</div>
          </div>`;
      }
      messagesContainer.appendChild(messageEl);

      // Ensure messagesContainer is scrollable
      if (messagesContainer) {
        const computedStyle = window.getComputedStyle(messagesContainer);
        if (
          (computedStyle.overflowY !== 'auto' && computedStyle.overflowY !== 'scroll') ||
          computedStyle.height === 'auto' ||
          computedStyle.height === '0px'
        ) {
          messagesContainer.style.overflowY = 'auto';
          if (!messagesContainer.style.height) {
            messagesContainer.style.height = '300px'; // Set a reasonable default height
          }
        }
      }

      if (document.getElementById('auto-scroll-switch')?.checked) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    };
  }
}

window.UIStructureBuilder = UIStructureBuilder;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    UIStructureBuilder.buildCompleteInterface();
  });
} else {
  UIStructureBuilder.buildCompleteInterface();
}
