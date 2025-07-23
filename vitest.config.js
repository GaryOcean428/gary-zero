import { defineConfig } from "vitest/config";
import { resolve } from "path";

export default defineConfig({
    test: {
        globals: true,
        environment: "jsdom",
        setupFiles: ["./tests/setup.js"],
        testTimeout: 30000,
        hookTimeout: 10000,
        coverage: {
            provider: "v8",
            reporter: ["text", "json", "html", "lcov"],
            reportsDirectory: "./coverage",
            threshold: {
                global: {
                    branches: 80,
                    functions: 80,
                    lines: 80,
                    statements: 80,
                },
            },
            exclude: [
                "node_modules/",
                "tests/",
                "coverage/",
                "*.config.js",
                "*.config.ts",
                "dist/",
                "build/",
                "webui/js/alpine*.js",
                "webui/js/transformers*.js",
                "webui/lib/",
                "scripts/",
                "**/*.min.js",
                "**/*.d.ts",
                "**/types.ts",
                "docs/",
                "tmp/",
                "logs/",
                "memory/",
                "prompts/",
                "knowledge/",
                "instruments/"
            ],
            include: [
                "webui/**/*.js",
                "lib/**/*.js",
                "framework/**/*.js"
            ]
        },
        include: [
            "tests/**/*.{test,spec}.{js,ts}",
            "webui/**/*.{test,spec}.{js,ts}",
            "framework/**/*.{test,spec}.{js,ts}",
        ],
        exclude: [
            "node_modules/", 
            "dist/", 
            "build/", 
            "**/*.min.js",
            "tmp/",
            "logs/",
            "memory/",
            "prompts/",
            "knowledge/",
            "instruments/"
        ],
        // Performance monitoring
        benchmark: {
            include: ["tests/**/*.{bench,benchmark}.{js,ts}"],
            exclude: ["node_modules/"],
            reporter: ["default", "json"],
            outputFile: {
                json: "./benchmark-results.json"
            }
        },
        // Railway-compatible settings for CI
        pool: "forks",
        poolOptions: {
            forks: {
                singleFork: process.env.CI === "true",
                minForks: process.env.CI === "true" ? 1 : 2,
                maxForks: process.env.CI === "true" ? 2 : 4,
            },
        },
        // Mock external dependencies in CI
        server: {
            deps: {
                external: ["fs", "path", "os", "crypto"]
            }
        }
    },
    resolve: {
        alias: {
            "@": resolve(process.cwd(), "./webui"),
            "@components": resolve(process.cwd(), "./webui/js"),
            "@lib": resolve(process.cwd(), "./lib"),
            "@framework": resolve(process.cwd(), "./framework"),
            "@tests": resolve(process.cwd(), "./tests"),
        },
    },
    // Define globals for testing environment
    define: {
        "process.env.NODE_ENV": '"test"',
        "process.env.VITEST": "true"
    }
});
