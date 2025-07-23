import { defineConfig } from 'vite';

export default defineConfig({
  // Define environment variables for browser-safe access
  define: {
    // Replace process.env.NODE_ENV with import.meta.env.MODE
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    // Add other environment variables as needed
    'process.env.DEV': JSON.stringify(process.env.NODE_ENV === 'development'),
  },
  
  // Server configuration
  server: {
    port: process.env.PORT || 5173,
    host: process.env.HOST || 'localhost',
    // Enable CORS for development
    cors: true,
  },
  
  // Build configuration
  build: {
    // Output directory
    outDir: 'dist',
    // Generate source maps for debugging
    sourcemap: process.env.NODE_ENV === 'development',
    // Minify in production
    minify: process.env.NODE_ENV === 'production',
    // Ensure browser compatibility
    target: 'es2015',
    // Roll up options for better tree shaking
    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: {
          vendor: ['alpine'],
        },
      },
    },
  },
  
  // Plugin configuration (add plugins as needed)
  plugins: [],
  
  // Resolve configuration
  resolve: {
    // Add file extensions to resolve
    extensions: ['.js', '.ts', '.json'],
  },
  
  // Environment variable prefix for client-side access
  envPrefix: 'VITE_',
});