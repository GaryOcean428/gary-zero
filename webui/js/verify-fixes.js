// CSP and Alpine.js Fix Verification Script
// Run this in the browser console to verify fixes

(() => {
    console.log("🔍 Running CSP and Alpine.js fix verification...\n");

    const tests = [];

    // Test 1: CSP Meta Tag
    function testCSPMeta() {
        const meta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        const hasUnsafeEval = meta?.content.includes("unsafe-eval");
        const hasExternalDomains =
            meta?.content.includes("cdnjs.cloudflare.com") && meta?.content.includes("fonts.googleapis.com");

        return {
            name: "CSP Meta Tag",
            passed: meta && hasUnsafeEval && hasExternalDomains,
            message: meta
                ? hasUnsafeEval
                    ? hasExternalDomains
                        ? "CSP properly configured"
                        : "CSP missing external domains"
                    : "CSP missing unsafe-eval for Alpine.js"
                : "CSP meta tag not found",
            details: meta ? meta.content : "N/A",
        };
    }

    // Test 2: Alpine.js Eval Capability
    function testAlpineEval() {
        try {
            // Test if Function constructor works (needed for Alpine.js)
            const testFunc = new Function("return true");
            const result = testFunc();

            return {
                name: "Alpine.js Eval Support",
                passed: result === true,
                message:
                    result === true
                        ? "Function constructor works - Alpine.js should function"
                        : "Function constructor blocked",
                details: "Function constructor test completed",
            };
        } catch (e) {
            return {
                name: "Alpine.js Eval Support",
                passed: false,
                message: `Eval still blocked: ${e.message}`,
                details: e.toString(),
            };
        }
    }

    // Test 3: External Stylesheet Loading
    function testStylesheets() {
        const stylesheets = Array.from(document.styleSheets);
        const external = stylesheets.filter((s) => {
            try {
                return s.href && !s.href.startsWith(window.location.origin);
            } catch (e) {
                return false;
            }
        });

        return {
            name: "External Stylesheets",
            passed: external.length > 0,
            message: `${external.length} external stylesheets loaded`,
            details: external.map((s) => s.href).join(", "),
        };
    }

    // Test 4: ToastManager Container
    function testToastManager() {
        const containers = document.querySelectorAll(
            "#toast-container, #toast-container-enhanced, #toast-container-fallback"
        );
        const hasToastManager = typeof ToastManager !== "undefined";
        const hasGlobalInstance = typeof window.toastManager !== "undefined";

        return {
            name: "ToastManager",
            passed: containers.length > 0 && hasToastManager,
            message: `${containers.length} container(s) found, ToastManager: ${hasToastManager}, Global instance: ${hasGlobalInstance}`,
            details: Array.from(containers)
                .map((c) => c.id)
                .join(", "),
        };
    }

    // Test 5: Alpine.js Availability and Components
    function testAlpineComponents() {
        const hasAlpine = typeof Alpine !== "undefined";
        const hasVersion = hasAlpine && Alpine.version;
        const hasCustomComponents = hasAlpine && Alpine._components && Alpine._components.has("appState");

        return {
            name: "Alpine.js Components",
            passed: hasAlpine && hasCustomComponents,
            message: hasAlpine
                ? hasCustomComponents
                    ? `Alpine.js v${hasVersion} with custom components loaded`
                    : "Alpine.js loaded but missing custom components"
                : "Alpine.js not available",
            details: hasAlpine ? `Version: ${hasVersion}` : "N/A",
        };
    }

    // Test 6: DOM Elements Availability
    function testDOMElements() {
        const requiredElements = ["#right-panel", "#chat-input", "#send-button", "#chat-history", "#input-section"];

        const found = requiredElements.filter((sel) => document.querySelector(sel));

        return {
            name: "Required DOM Elements",
            passed: found.length === requiredElements.length,
            message: `${found.length}/${requiredElements.length} required elements found`,
            details: `Found: ${found.join(", ")}`,
        };
    }

    // Test 7: Console Error Check
    function testConsoleErrors() {
        // This is a manual check since we can't access console errors directly
        return {
            name: "Console Errors (Manual Check)",
            passed: null, // Manual verification required
            message: "Please check browser console for CSP violations or Alpine.js errors",
            details: 'Look for "Content Security Policy" or "unsafe-eval" errors',
        };
    }

    // Run all tests
    const allTests = [
        testCSPMeta(),
        testAlpineEval(),
        testStylesheets(),
        testToastManager(),
        testAlpineComponents(),
        testDOMElements(),
        testConsoleErrors(),
    ];

    // Display results
    console.log("📊 VERIFICATION RESULTS\n");
    console.log("═".repeat(50));

    allTests.forEach((result) => {
        const icon = result.passed === true ? "✅" : result.passed === false ? "❌" : "⚠️";
        console.log(`${icon} ${result.name}: ${result.message}`);
        if (result.details) {
            console.log(`   Details: ${result.details}`);
        }
        console.log("");
    });

    const passedCount = allTests.filter((r) => r.passed === true).length;
    const totalCount = allTests.filter((r) => r.passed !== null).length;

    console.log(`Overall: ${passedCount}/${totalCount} automated tests passed`);
    console.log("");

    // Additional diagnostic info
    console.log("🔧 DIAGNOSTIC INFORMATION\n");
    console.log("═".repeat(50));
    console.log("User Agent:", navigator.userAgent);
    console.log("Document Ready State:", document.readyState);
    console.log("Alpine.js Available:", typeof Alpine !== "undefined");
    console.log("ToastManager Available:", typeof ToastManager !== "undefined");

    if (typeof Alpine !== "undefined") {
        console.log("Alpine.js Version:", Alpine.version || "Unknown");
        console.log("Alpine.js Started:", Alpine.version ? "Yes" : "No");
    }

    console.log("");
    console.log("✅ Verification complete! Check results above.");

    // Return results for programmatic access
    return {
        results: allTests,
        summary: {
            passed: passedCount,
            total: totalCount,
            success: passedCount === totalCount,
        },
    };
})();
