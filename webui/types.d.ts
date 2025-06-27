// Global type definitions for the project

declare global {
  interface Window {
    // Core functions
    newChat: () => Promise<void>;
    resetChat: (ctxid?: string | null) => Promise<void>;
    killChat: (id: string) => Promise<void>;
    selectChat: (id: string) => Promise<void>;
    
    // Message and communication
    sendMessage: () => Promise<void>;
    sendJsonData: (url: string, data: any) => Promise<any>;
    updateChatInput: (text: string) => void;
    setMessage: (id: string, type: string, heading: string, content: string, temp: boolean, kvps?: any) => HTMLElement;
    
    // Context management
    setContext: (id: string) => void;
    getContext: () => string;
    switchFromContext: (id: string) => void;
    
    // UI state management
    toggleAutoScroll: (autoScroll: boolean) => Promise<void>;
    toggleJson: (showJson: boolean) => Promise<void>;
    toggleThoughts: (showThoughts: boolean) => Promise<void>;
    toggleUtils: (showUtils: boolean) => Promise<void>;
    toggleDarkMode: (isDark: boolean) => void;
    toggleSpeech: (isOn: boolean) => void;
    
    // Agent control
    pauseAgent: (paused: boolean) => Promise<void>;
    nudge: () => Promise<void>;
    restart: () => Promise<void>;
    
    // File management
    loadChats: () => Promise<void>;
    saveChat: () => Promise<void>;
    handleFileUpload: (event: Event) => void;
    handleFileUploadForAlpine: (event: Event) => void;
    
    // Utility functions
    toast: (text: string, type?: 'info' | 'success' | 'error' | 'warning', timeout?: number) => void;
    toastFetchError: (text: string, error: Error) => void;
    safeCall: (name: string, ...args: any[]) => void;
    
    // Task management
    openTaskDetail: (taskId: string) => void;
    
    // Speech functionality
    speech: {
      speak: (text: string) => void;
      stop: () => void;
      isSpeaking: () => boolean;
    };
  }

  // Alpine.js global
  var Alpine: {
    $data: (element: Element) => any;
    directive: (name: string, callback: any) => void;
    store: (name: string, data: any) => void;
  };

  // Element extensions for Alpine.js
  interface Element {
    __x?: {
      $data: any;
    };
  }

  // HTML element extensions
  interface HTMLElement {
    timeoutId?: number;
  }
}

export {};