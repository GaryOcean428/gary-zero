// Import enhanced logger
import { logger } from './console-logger.js';

// Tunnel settings for the Settings modal
document.addEventListener("alpine:init", () => {
    Alpine.data("tunnelSettings", () => ({
        isLoading: false,
        tunnelLink: "",
        linkGenerated: false,
        loadingText: "",
        isStopping: false,

        init() {
            this.checkTunnelStatus();
        },

        async checkTunnelStatus() {
            try {
                const response = await fetch("/tunnel_proxy", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ action: "get" }),
                });

                const data = await response.json();

                if (data.success && data.tunnel_url) {
                    // Update the stored URL if it's different from what we have
                    if (this.tunnelLink !== data.tunnel_url) {
                        this.tunnelLink = data.tunnel_url;
                        localStorage.setItem("agent_zero_tunnel_url", data.tunnel_url);
                    }
                    this.linkGenerated = true;
                } else {
                    // Check if we have a stored tunnel URL
                    const storedTunnelUrl = localStorage.getItem("agent_zero_tunnel_url");

                    if (storedTunnelUrl) {
                        // Use the stored URL but verify it's still valid
                        const verifyResponse = await fetch("/tunnel_proxy", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify({ action: "verify", url: storedTunnelUrl }),
                        });

                        const verifyData = await verifyResponse.json();

                        if (verifyData.success && verifyData.is_valid) {
                            this.tunnelLink = storedTunnelUrl;
                            this.linkGenerated = true;
                        } else {
                            // Clear stale URL
                            localStorage.removeItem("agent_zero_tunnel_url");
                            this.tunnelLink = "";
                            this.linkGenerated = false;
                        }
                    } else {
                        // No stored URL, show the generate button
                        this.tunnelLink = "";
                        this.linkGenerated = false;
                    }
                }
            } catch {
                // Error checking tunnel status - reset state
                this.tunnelLink = "";
                this.linkGenerated = false;
            }
        },

        async refreshLink() {
            // Call generate but with a confirmation first
            if (confirm("Are you sure you want to generate a new tunnel URL? The old URL will no longer work.")) {
                this.isLoading = true;
                this.loadingText = "Refreshing tunnel...";

                // Change refresh button appearance
                const refreshButton = document.querySelector(".refresh-link-button");
                const originalContent = refreshButton.innerHTML;
                refreshButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
                refreshButton.disabled = true;
                refreshButton.classList.add("refreshing");

                try {
                    // First stop any existing tunnel
                    const stopResponse = await fetch("/tunnel_proxy", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ action: "stop" }),
                    });

                    // Check if stopping was successful
                    const stopData = await stopResponse.json();
                    if (!stopData.success) {
                        // Continue anyway since we want to create a new one
                    }

                    // Then generate a new one
                    await this.generateLink();
                } catch {
                    // Error generating tunnel link
                    this.isLoading = false;
                    this.tunnelLink = "";
                    this.linkGenerated = false;
                } finally {
                    // Reset refresh button
                    refreshButton.innerHTML = originalContent;
                    refreshButton.disabled = false;
                    refreshButton.classList.remove("refreshing");
                }
            }
        },

        async generateLink() {
            // First check if authentication is enabled
            try {
                const authCheckResponse = await fetch("/settings_get");
                const authData = await authCheckResponse.json();

                // Find the auth_login and auth_password in the settings
                let hasAuth = false;

                if (authData && authData.settings && authData.settings.sections) {
                    for (const section of authData.settings.sections) {
                        if (section.fields) {
                            const authLoginField = section.fields.find((field) => field.id === "auth_login");
                            const authPasswordField = section.fields.find((field) => field.id === "auth_password");

                            if (
                                authLoginField &&
                                authPasswordField &&
                                authLoginField.value &&
                                authPasswordField.value
                            ) {
                                hasAuth = true;
                                break;
                            }
                        }
                    }
                }

                // If no authentication is set, warn the user
                if (!hasAuth) {
                    const proceed = confirm(
                        "WARNING: No authentication is configured for your Gary-Zero instance.\n\n" +
                            "Creating a public tunnel without authentication means anyone with the URL " +
                            "can access your Gary-Zero instance.\n\n" +
                            "It is recommended to set up authentication in the Settings > Authentication section " +
                            "before creating a public tunnel.\n\n" +
                            "Do you want to proceed anyway?"
                    );

                    if (!proceed) {
                        return; // User cancelled
                    }
                }
            } catch {
                // Continue anyway if we can't check auth status
            }

            this.isLoading = true;
            this.loadingText = "Creating tunnel...";

            // Get provider from the parent settings modal scope
            const modalEl = document.getElementById("settingsModal");
            const modalAD = Alpine.$data(modalEl);
            const provider = modalAD.provider || "serveo"; // Default to serveo if not set

            // Change create button appearance
            const createButton = document.querySelector(".tunnel-actions .btn-ok");
            if (createButton) {
                createButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
                createButton.disabled = true;
                createButton.classList.add("creating");
            }

            try {
                // Call the backend API to create a tunnel
                const response = await fetch("/tunnel_proxy", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        action: "create",
                        provider: provider,
                        // port: window.location.port || (window.location.protocol === 'https:' ? 443 : 80)
                    }),
                });

                const data = await response.json();

                if (data.success && data.tunnel_url) {
                    // Store the tunnel URL in localStorage for persistence
                    localStorage.setItem("agent_zero_tunnel_url", data.tunnel_url);

                    this.tunnelLink = data.tunnel_url;
                    this.linkGenerated = true;

                    // Show success message to confirm creation
                    window.toast("Tunnel created successfully", "success", 3000);
                } else {
                    // The tunnel might still be starting up, check again after a delay
                    this.loadingText = "Tunnel creation taking longer than expected...";

                    // Wait for 5 seconds and check if the tunnel is running
                    await new Promise((resolve) => setTimeout(resolve, 5000));

                    // Check if tunnel is running now
                    try {
                        const statusResponse = await fetch("/tunnel_proxy", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify({ action: "get" }),
                        });

                        const statusData = await statusResponse.json();

                        if (statusData.success && statusData.tunnel_url) {
                            // Tunnel is now running, we can update the UI
                            localStorage.setItem("agent_zero_tunnel_url", statusData.tunnel_url);
                            this.tunnelLink = statusData.tunnel_url;
                            this.linkGenerated = true;
                            window.toast("Tunnel created successfully", "success", 3000);
                            return;
                        }
                    } catch {
                        // Error accessing tunnel status
                        this.tunnelLink = "";
                        this.linkGenerated = false;
                    }

                    // If we get here, the tunnel really failed to start
                    const errorMessage = data.message || "Failed to create tunnel. Please try again.";
                    window.toast(errorMessage, "error", 5000);
                }
            } catch {
                // Error generating tunnel link
                this.isLoading = false;
                this.tunnelLink = "";
                this.linkGenerated = false;
            } finally {
                this.isLoading = false;
                this.loadingText = "";

                // Reset create button if it's still in the DOM
                const createButton = document.querySelector(".tunnel-actions .btn-ok");
                if (createButton) {
                    createButton.innerHTML = '<i class="fas fa-play-circle"></i> Create Tunnel';
                    createButton.disabled = false;
                    createButton.classList.remove("creating");
                }
            }
        },

        async stopTunnel() {
            if (confirm("Are you sure you want to stop the tunnel? The URL will no longer be accessible.")) {
                this.isLoading = true;
                this.isStopping = true;
                this.loadingText = "Stopping tunnel...";

                try {
                    // Call the backend to stop the tunnel
                    const response = await fetch("/tunnel_proxy", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ action: "stop" }),
                    });

                    const data = await response.json();

                    if (data.success) {
                        // Clear the stored URL
                        localStorage.removeItem("agent_zero_tunnel_url");

                        // Update UI state
                        this.tunnelLink = "";
                        this.linkGenerated = false;

                        window.toast("Tunnel stopped successfully", "success", 3000);
                    } else {
                        window.toast("Failed to stop tunnel", "error", 3000);
                    }
                } catch {
                    // Error stopping tunnel
                    this.isLoading = false;
                } finally {
                    this.isLoading = false;
                    this.isStopping = false;
                    this.loadingText = "";
                }
            }
        },

        async copyToClipboard() {
            try {
                await navigator.clipboard.writeText(this.tunnelLink);
                // Successfully copied to clipboard
            } catch {
                // Fallback for older browsers or restricted environments
                const textArea = document.createElement("textarea");
                textArea.value = this.tunnelLink;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand("copy");
                document.body.removeChild(textArea);
            }
        },
    }));
});
