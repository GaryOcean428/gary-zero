"""
Simple CLI-based approval interface for demonstration.

This module provides a basic command-line interface for approval requests
that can be integrated with web UI or other interface systems.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
from .approval_workflow import ApprovalRequest, ApprovalWorkflow


class CLIApprovalInterface:
    """Command-line interface for approval requests."""
    
    def __init__(self, workflow: ApprovalWorkflow):
        self.workflow = workflow
        self.pending_display = {}
        
        # Set up callbacks
        self.workflow.set_approval_callback(self.display_approval_request)
        self.workflow.set_response_callback(self.handle_approval_response)
    
    def display_approval_request(self, request: ApprovalRequest) -> None:
        """Display approval request to user via CLI."""
        print("\n" + "="*60)
        print("🔐 APPROVAL REQUIRED")
        print("="*60)
        print(f"User: {request.user_id}")
        print(f"Action: {request.action_type}")
        print(f"Risk Level: {request.risk_level.value.upper()}")
        print(f"Description: {request.action_description}")
        print(f"Request ID: {request.request_id}")
        
        if request.parameters:
            print(f"Parameters:")
            for key, value in request.parameters.items():
                # Truncate long values
                display_value = str(value)[:100]
                if len(str(value)) > 100:
                    display_value += "..."
                print(f"  {key}: {display_value}")
        
        # Calculate time remaining
        time_remaining = request.expires_at - time.time()
        print(f"Time Remaining: {int(time_remaining)} seconds")
        
        print("\nTo approve this request, run:")
        print(f"  approve {request.request_id}")
        print("To reject this request, run:")
        print(f"  reject {request.request_id} [reason]")
        print("="*60)
        
        # Store for reference
        self.pending_display[request.request_id] = request
    
    def handle_approval_response(self, request: ApprovalRequest, approved: bool) -> None:
        """Handle approval response."""
        status = "APPROVED" if approved else "REJECTED"
        print(f"\n✅ Request {request.request_id} {status}")
        
        # Remove from pending display
        if request.request_id in self.pending_display:
            del self.pending_display[request.request_id]
    
    async def process_command(self, command: str) -> str:
        """Process CLI command for approval management."""
        parts = command.strip().split()
        if not parts:
            return "No command provided"
        
        cmd = parts[0].lower()
        
        if cmd == "approve":
            if len(parts) < 2:
                return "Usage: approve <request_id> [note]"
            
            request_id = parts[1]
            note = " ".join(parts[2:]) if len(parts) > 2 else None
            
            success = await self.workflow.approve_request(request_id, "cli_user", note)
            return f"Request {request_id} {'approved' if success else 'not found or expired'}"
        
        elif cmd == "reject":
            if len(parts) < 2:
                return "Usage: reject <request_id> [reason]"
            
            request_id = parts[1]
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Rejected via CLI"
            
            success = await self.workflow.reject_request(request_id, "cli_user", reason)
            return f"Request {request_id} {'rejected' if success else 'not found or expired'}"
        
        elif cmd == "list":
            pending = self.workflow.get_pending_requests()
            if not pending:
                return "No pending approval requests"
            
            result = "Pending approval requests:\n"
            for req in pending:
                time_remaining = int(req.expires_at - time.time())
                result += f"  {req.request_id}: {req.action_type} (user: {req.user_id}, {time_remaining}s remaining)\n"
            return result
        
        elif cmd == "status":
            stats = self.workflow.get_approval_statistics()
            return json.dumps(stats, indent=2)
        
        elif cmd == "help":
            return """
Available commands:
  approve <request_id> [note]  - Approve a pending request
  reject <request_id> [reason] - Reject a pending request  
  list                         - List all pending requests
  status                       - Show approval statistics
  help                         - Show this help message
"""
        
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."


class WebUIApprovalInterface:
    """Web UI interface for approval requests (mock implementation)."""
    
    def __init__(self, workflow: ApprovalWorkflow):
        self.workflow = workflow
        self.pending_requests = {}
        
        # Set up callbacks
        self.workflow.set_approval_callback(self.queue_approval_request)
        self.workflow.set_response_callback(self.handle_approval_response)
    
    def queue_approval_request(self, request: ApprovalRequest) -> None:
        """Queue approval request for web UI display."""
        self.pending_requests[request.request_id] = {
            "request": request,
            "timestamp": time.time(),
            "displayed": False
        }
        
        # In a real implementation, this would notify the web UI
        print(f"📱 New approval request queued for web UI: {request.request_id}")
    
    def handle_approval_response(self, request: ApprovalRequest, approved: bool) -> None:
        """Handle approval response from web UI."""
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]
        
        # In a real implementation, this would update the web UI
        status = "approved" if approved else "rejected"
        print(f"🌐 Web UI: Request {request.request_id} {status}")
    
    def get_pending_requests_for_ui(self) -> Dict[str, Any]:
        """Get pending requests formatted for web UI."""
        ui_requests = {}
        
        for request_id, data in self.pending_requests.items():
            request = data["request"]
            ui_requests[request_id] = {
                "user_id": request.user_id,
                "action_type": request.action_type,
                "action_description": request.action_description,
                "risk_level": request.risk_level.value,
                "parameters": request.parameters,
                "created_at": request.created_at,
                "expires_at": request.expires_at,
                "time_remaining": max(0, request.expires_at - time.time()),
                "request_data": request.to_dict()
            }
        
        return ui_requests
    
    async def handle_ui_response(self, request_id: str, action: str, 
                                user_id: str, reason: Optional[str] = None) -> bool:
        """Handle approval response from web UI."""
        if action.lower() == "approve":
            return await self.workflow.approve_request(request_id, user_id, reason)
        elif action.lower() == "reject":
            return await self.workflow.reject_request(request_id, user_id, reason)
        else:
            return False


def create_approval_interface(workflow: ApprovalWorkflow, interface_type: str = "cli"):
    """Factory function to create appropriate approval interface."""
    if interface_type.lower() == "cli":
        return CLIApprovalInterface(workflow)
    elif interface_type.lower() == "web":
        return WebUIApprovalInterface(workflow)
    else:
        raise ValueError(f"Unknown interface type: {interface_type}")


# Example usage and demonstration
async def demo_approval_interface():
    """Demonstrate the approval interface."""
    from .approval_workflow import ApprovalWorkflow
    from .audit_logger import AuditLogger
    
    # Create workflow and interface
    workflow = ApprovalWorkflow(AuditLogger())
    workflow.set_user_role("demo_user", "admin")
    
    cli_interface = CLIApprovalInterface(workflow)
    
    print("Approval Interface Demo")
    print("=" * 40)
    
    # Simulate an approval request
    print("\n1. Simulating approval request...")
    
    async def mock_request():
        return await workflow.request_approval(
            user_id="demo_user",
            action_type="file_delete",
            action_description="Delete important system file",
            parameters={"file": "/etc/passwd", "force": True},
            timeout_override=30
        )
    
    # Start the request
    request_task = asyncio.create_task(mock_request())
    
    # Wait a bit for the request to be displayed
    await asyncio.sleep(1)
    
    # Show how to interact with CLI
    print("\n2. CLI Commands available:")
    print(await cli_interface.process_command("help"))
    
    print("\n3. List pending requests:")
    print(await cli_interface.process_command("list"))
    
    # Auto-approve for demo (in real use, user would type this)
    print("\n4. Auto-approving request for demo...")
    pending = workflow.get_pending_requests()
    if pending:
        request_id = pending[0].request_id
        result = await cli_interface.process_command(f"approve {request_id} Demo approval")
        print(result)
    
    # Wait for the request to complete
    try:
        approved = await asyncio.wait_for(request_task, timeout=5)
        print(f"\n5. Request result: {'Approved' if approved else 'Rejected'}")
    except asyncio.TimeoutError:
        print("\n5. Request timed out")
    
    # Show statistics
    print("\n6. Final statistics:")
    print(await cli_interface.process_command("status"))


if __name__ == "__main__":
    asyncio.run(demo_approval_interface())