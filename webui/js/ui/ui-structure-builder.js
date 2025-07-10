export class UIStructureBuilder {
    static buildCompleteInterface() {
        // Don't override the existing HTML structure
        // Just ensure essential elements exist
        const requiredElements = [
            "right-panel",
            "chat-input",
            "send-button",
            "chat-history",
            "input-section",
            "auto-scroll-switch",
        ];

        const missing = [];
        requiredElements.forEach((id) => {
            if (!document.getElementById(id)) {
                missing.push(id);
            }
        });

        if (missing.length > 0) {
            return;
        }

        UIStructureBuilder.initializeMessageHandlers();
        return;
    }

    static initializeMessageHandlers() {
        const chatInput = document.getElementById("chat-input");
        if (chatInput) {
            chatInput.addEventListener("input", function () {
                this.style.height = "auto";
                this.style.height = `${this.scrollHeight}px`;
            });
            chatInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    document.getElementById("send-button")?.click();
                }
            });
        }

        window.renderMessage = (type, content, metadata = {}) => {
            const messagesContainer = document.querySelector("#chat-history");
            if (!messagesContainer) return;
            const messageEl = document.createElement("div");
            messageEl.className = `message ${type}`;
            if (type === "agent") {
                messageEl.innerHTML = `
          <div class="message-content">
            <div class="message-header">Agent ${metadata.agentId || "0"}: ${metadata.status || "Responding"}</div>
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

            if (document.getElementById("auto-scroll-switch")?.checked) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        };
    }
}

window.UIStructureBuilder = UIStructureBuilder;
