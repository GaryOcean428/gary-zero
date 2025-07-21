import { defineConfig } from "vitest/config";
import { resolve } from "path";

export default defineConfig({
    test: {
        globals: true,
        environment: "jsdom",
        setupFiles: ["./tests/setup.js"],
        coverage: {
            provider: "v8",
            reporter: ["text", "json", "html"],
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
            ],
        },
        include: [
            "tests/**/*.{test,spec}.{js,ts}",
            "webui/**/*.{test,spec}.{js,ts}",
            "framework/**/*.{test,spec}.{js,ts}",
        ],
        exclude: ["node_modules/", "dist/", "build/", "**/*.min.js"],
        // Railway-compatible settings
        pool: "forks",
        poolOptions: {
            forks: {
                singleFork: true,
            },
        },
    },
    resolve: {
        alias: {
            "@": resolve(process.cwd(), "./webui"),
            "@components": resolve(process.cwd(), "./webui/js"),
            "@lib": resolve(process.cwd(), "./lib"),
            "@framework": resolve(process.cwd(), "./framework"),
        },
    },
});
