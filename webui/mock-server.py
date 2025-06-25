#!/usr/bin/env python3
"""
Simple mock backend server for Zero project web UI testing
Handles the expected POST endpoints to prevent 501 errors during development
"""

import json
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import os

class MockBackendHandler(http.server.SimpleHTTPRequestHandler):
    """Mock backend handler that serves static files and handles API endpoints"""
    
    def do_POST(self):
        """Handle POST requests to API endpoints"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except json.JSONDecodeError:
            data = {}
        
        if self.path == '/poll':
            self.handle_poll(data)
        elif self.path == '/send':
            self.handle_send(data)
        elif self.path == '/reset':
            self.handle_reset(data)
        elif self.path == '/new_chat':
            self.handle_new_chat(data)
        else:
            # Return 404 for unknown endpoints
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": f"Unknown endpoint: {self.path}"}
            self.wfile.write(json.dumps(response).encode())
    
    def handle_poll(self, data):
        """Handle /poll endpoint - returns mock status and logs"""
        response = {
            "log_version": 1,
            "log_guid": "mock-guid-123",
            "logs": [],
            "log_progress": "",
            "log_progress_active": False,
            "paused": False,
            "contexts": [],
            "tasks": [],
            "connected": True,
            "status": "ready"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_send(self, data):
        """Handle /send endpoint - mock message sending"""
        response = {
            "success": True,
            "message": "Message sent successfully (mock)",
            "id": f"msg-{datetime.now().timestamp()}"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_reset(self, data):
        """Handle /reset endpoint - mock chat reset"""
        response = {
            "success": True,
            "message": "Chat reset successfully (mock)"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_new_chat(self, data):
        """Handle /new_chat endpoint - mock new chat creation"""
        response = {
            "success": True,
            "chat_id": f"chat-{datetime.now().timestamp()}",
            "message": "New chat created successfully (mock)"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to provide cleaner logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def run_mock_server(port=8080):
    """Run the mock backend server"""
    try:
        # Change to webui directory to serve static files
        webui_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(webui_dir)
        
        print(f"Mock Zero backend server running at http://localhost:{port}")
        print(f"Serving files from: {webui_dir}")
        print("Supported endpoints:")
        print("  GET  /          - Web UI")
        print("  POST /poll      - Status polling")
        print("  POST /send      - Send messages")
        print("  POST /reset     - Reset chat")
        print("  POST /new_chat  - Create new chat")
        print("\nPress Ctrl+C to stop the server")
        
        with socketserver.TCPServer(("", port), MockBackendHandler) as httpd:
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nShutting down mock server...")
    except Exception as e:
        print(f"Error starting mock server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Mock server stopped.")

if __name__ == "__main__":
    run_mock_server()
