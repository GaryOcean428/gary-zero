// Example MCP server implementation using TypeScript and Yarn as specified in the problem statement
// This demonstrates the @modelcontextprotocol/sdk usage with Yarn 4.9.2+

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { 
  CallToolRequestSchema, 
  ListResourcesRequestSchema, 
  ListToolsRequestSchema, 
  ReadResourceRequestSchema 
} from '@modelcontextprotocol/sdk/types.js';

// MCP Server implementation following the problem statement guidelines
class GaryZeroMcpServer {
  private server: Server;

  constructor() {
    this.server = new Server({
      name: "gary-zero-mcp",
      version: "1.0.0"
    }, {
      capabilities: {
        tools: {},
        resources: {}
      }
    });

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "greet",
            description: "Greet a user with their name",
            inputSchema: {
              type: "object",
              properties: {
                name: {
                  type: "string",
                  description: "Name of the person to greet"
                }
              },
              required: ["name"]
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === "greet") {
        const { name: userName } = args as { name: string };
        return {
          content: [
            {
              type: "text",
              text: `Hello, ${userName}! Welcome to Gary-Zero AI Agent Framework.`
            }
          ]
        };
      }

      throw new Error(`Unknown tool: ${name}`);
    });

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: "gary-zero://status",
            name: "Gary-Zero Status",
            description: "Current status of the Gary-Zero framework",
            mimeType: "application/json"
          }
        ]
      };
    });

    // Handle resource reads
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      if (uri === "gary-zero://status") {
        return {
          contents: [
            {
              uri,
              mimeType: "application/json",
              text: JSON.stringify({
                status: "healthy",
                timestamp: new Date().toISOString(),
                framework: "Gary-Zero AI Agent Framework",
                version: "0.9.0"
              }, null, 2)
            }
          ]
        };
      }

      throw new Error(`Unknown resource: ${uri}`);
    });
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Gary-Zero MCP Server started"); // Use stderr for logging
  }
}

// Start the server
const server = new GaryZeroMcpServer();
server.start().catch((error) => {
  console.error("Failed to start MCP server:", error);
  process.exit(1);
});