// UI Tab Management for Sidebar
class SidebarTabManager {
    constructor() {
        this.activeTab = "chats"; // Default to chats tab
        this.init();
    }

    init() {
        // Add click handlers to tabs
        const chatsTab = document.getElementById("chats-tab");
        const tasksTab = document.getElementById("tasks-tab");

        if (chatsTab) {
            chatsTab.addEventListener("click", () => this.switchTab("chats"));
        }

        if (tasksTab) {
            tasksTab.addEventListener("click", () => this.switchTab("tasks"));
        }

        // Ensure initial state is correct
        this.updateTabDisplay();
    }

    switchTab(tabName) {
        try {
            this.activeTab = tabName;
            this.updateTabDisplay();

            // Store preference
            localStorage.setItem("sidebarActiveTab", tabName);

            console.log(`✅ Switched to ${tabName} tab`);
        } catch (error) {
            console.error("❌ Error switching sidebar tab:", error);
        }
    }

    updateTabDisplay() {
        // Update tab appearance
        const chatsTab = document.getElementById("chats-tab");
        const tasksTab = document.getElementById("tasks-tab");
        const chatsSection = document.getElementById("chats-section");
        const tasksSection = document.getElementById("tasks-section");

        if (chatsTab && tasksTab && chatsSection && tasksSection) {
            // Remove active class from all tabs
            chatsTab.classList.remove("active");
            tasksTab.classList.remove("active");
            chatsSection.classList.remove("active");
            tasksSection.classList.remove("active");

            // Add active class to current tab
            if (this.activeTab === "chats") {
                chatsTab.classList.add("active");
                chatsSection.classList.add("active");
                chatsSection.style.display = "block";
                tasksSection.style.display = "none";
            } else if (this.activeTab === "tasks") {
                tasksTab.classList.add("active");
                tasksSection.classList.add("active");
                tasksSection.style.display = "block";
                chatsSection.style.display = "none";
            }
        }
    }

    // Method to restore saved tab preference
    restoreTab() {
        const savedTab = localStorage.getItem("sidebarActiveTab");
        if (savedTab && (savedTab === "chats" || savedTab === "tasks")) {
            this.switchTab(savedTab);
        }
    }
}

// Initialize tab manager when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    try {
        window.sidebarTabManager = new SidebarTabManager();

        // Restore saved tab after a short delay to ensure all elements are loaded
        setTimeout(() => {
            window.sidebarTabManager.restoreTab();
        }, 100);

        console.log("✅ Sidebar tab manager initialized");
    } catch (error) {
        console.error("❌ Error initializing sidebar tab manager:", error);
    }
});

// Export for use by other modules
if (typeof module !== "undefined" && module.exports) {
    module.exports = SidebarTabManager;
} else {
    window.SidebarTabManager = SidebarTabManager;
}
