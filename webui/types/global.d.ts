// Global type declarations for Gary-Zero
declare global {
  // Alpine.js types
  interface Window {
    Alpine: {
      store: (name: string, data: any) => void;
      data: (element: Element) => any;
      directive: (name: string, callback: any) => void;
      version?: string;
    };
    ace: {
      edit: (id: string) => {
        setValue: (value: string) => void;
        getValue: () => string;
        clearSelection: () => void;
        navigateFileStart: () => void;
      };
    };
    vscodeTestWeb?: any;
    gideCodingAgent?: any;
    VSCodeWebIntegration?: any;
  }

  // API response types
  interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    detail?: any;
  }

  // MCP Server types
  interface McpServer {
    name: string;
    status: string;
    command?: string;
    args?: string[];
    env?: Record<string, string>;
  }

  // Settings types
  interface SettingsSection {
    id: string;
    fields: SettingsField[];
  }

  interface SettingsField {
    id: string;
    value: any;
  }

  interface SettingsProxy {
    settings: {
      sections: SettingsSection[];
    };
  }

  // Chat message types
  interface ChatMessage {
    id: string;
    type: string;
    heading: string;
    content: string;
    temp?: boolean;
    kvps?: Record<string, any>;
  }

  // Store types
  interface AlpineStore {
    [key: string]: any;
  }

  // Global functions
  const settingsModalProxy: SettingsProxy;
  const Alpine: Window['Alpine'];
  const ace: Window['ace'];
}

export {};