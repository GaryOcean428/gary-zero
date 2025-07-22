/**
 * Global type definitions for Gary Zero application
 */

// Alpine.js types
declare global {
  interface Window {
    Alpine: {
      store: (name: string) => any;
      $data: any;
      data: (name: string, fn: () => any) => void;
      directive: (name: string, fn: Function) => void;
      magic: (name: string, fn: Function) => void;
      start: () => void;
    };
    
    // Application globals
    settingsModalProxy: {
      settings: {
        sections: Array<{
          id: string;
          fields: Array<{
            id: string;
            value: any;
          }>;
        }>;
      };
    };
    
    // Utility functions
    openModal: (modalId: string) => void;
    toast: (message: string, type?: string) => void;
    showToast: (message: string, type?: string) => void;
    sendJsonData: (url: string, data: any) => Promise<any>;
    openFileLink: string | ((path: string) => void);
    
    // Speech and media
    SpeechSynthesisUtterance: any;
    MediaRecorder: any;
    webkitAudioContext: any;
    
    // External libraries
    ace: {
      edit: (element: string | HTMLElement) => {
        setValue: (value: string) => void;
        getValue: () => string;
        clearSelection: () => void;
        navigateFileStart: () => void;
        setTheme: (theme: string) => void;
        session: {
          setMode: (mode: string) => void;
        };
        on: (event: string, callback: Function) => void;
      };
    };
    flatpickr: any;
    DOMParser: any;
    ToastManager: any;
    renderMathInElement: any;
    
    // Feature flags
    ENABLE_DEV_FEATURES: boolean;
    VSCODE_INTEGRATION_ENABLED: boolean;
    CHAT_AUTO_RESIZE_ENABLED: boolean;
    
    // Message channels for VSCode integration
    messageChannels: any[];
    
    // Error handling
    ErrorBoundary: any;
    globalErrorBoundary: any;
    errorReporter: {
      reportError: (error: Error, context: any) => void;
    };
    
    // Application specific
    messageContent: string;
    resp: any;
  }
  
  // Node.js types for scripts that need it
  declare var process: {
    env: {
      NODE_ENV?: string;
      [key: string]: string | undefined;
    };
    cwd: () => string;
  };
  
  // Module declarations
  declare module "/js/*" {
    const content: any;
    export = content;
  }
  
  declare module "/components/*" {
    const content: any;
    export = content;
  }
}

export {};