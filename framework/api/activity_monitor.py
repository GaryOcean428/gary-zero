"""Activity monitor API for live browser and coding activity tracking."""

import json
import os
import time
from typing import Dict, List, Optional, Any
from threading import Lock
from datetime import datetime, timezone

from flask import Request, Response
from framework.helpers.api import ApiHandler, Input, Output
from framework.helpers.print_style import PrintStyle


class ActivityMonitor(ApiHandler):
    """API handler for monitoring live browser and coding activities."""
    
    _activities: List[Dict[str, Any]] = []
    _current_iframe_src: Optional[str] = None
    _activity_lock = Lock()
    _max_activities = 100  # Keep last 100 activities
    
    @classmethod
    def requires_auth(cls) -> bool:
        """Require authentication for activity monitoring."""
        return True
    
    async def process(self, input: Input, request: Request) -> Output:
        """Process activity monitoring requests."""
        action = input.get("action", "get_status")
        
        if action == "get_status":
            return self._get_status()
        elif action == "get_activities":
            return self._get_activities(input)
        elif action == "add_activity":
            return self._add_activity(input)
        elif action == "set_iframe_src":
            return self._set_iframe_src(input)
        elif action == "get_iframe_src":
            return self._get_iframe_src()
        elif action == "clear_activities":
            return self._clear_activities()
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}. Valid actions: get_status, get_activities, add_activity, set_iframe_src, get_iframe_src, clear_activities"
            }
    
    def _get_status(self) -> Dict[str, Any]:
        """Get current activity monitoring status."""
        with self._activity_lock:
            return {
                "success": True,
                "status": "active",
                "total_activities": len(self._activities),
                "current_iframe_src": self._current_iframe_src,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _get_activities(self, input: Input) -> Dict[str, Any]:
        """Get activity history with optional filtering."""
        limit = input.get("limit", 50)
        activity_type = input.get("type")  # Optional filter by type
        since = input.get("since")  # Optional timestamp filter
        
        with self._activity_lock:
            activities = self._activities.copy()
        
        # Filter by type if specified
        if activity_type:
            activities = [a for a in activities if a.get("type") == activity_type]
        
        # Filter by timestamp if specified
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                activities = [a for a in activities if 
                            datetime.fromisoformat(a.get("timestamp", "").replace('Z', '+00:00')) >= since_dt]
            except (ValueError, AttributeError):
                pass  # Ignore invalid timestamp
        
        # Limit results
        activities = activities[-limit:] if limit > 0 else activities
        
        return {
            "success": True,
            "activities": activities,
            "total": len(activities),
            "filtered": len(activities) < len(self._activities)
        }
    
    def _add_activity(self, input: Input) -> Dict[str, Any]:
        """Add a new activity to the monitor."""
        activity_type = input.get("type", "unknown")
        description = input.get("description", "")
        url = input.get("url")
        data = input.get("data", {})
        
        activity = {
            "id": f"activity_{int(time.time() * 1000)}",
            "type": activity_type,
            "description": description,
            "url": url,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with self._activity_lock:
            self._activities.append(activity)
            # Keep only the most recent activities
            if len(self._activities) > self._max_activities:
                self._activities = self._activities[-self._max_activities:]
        
        PrintStyle().debug(f"Activity added: {activity_type} - {description}")
        
        return {
            "success": True,
            "activity": activity
        }
    
    def _set_iframe_src(self, input: Input) -> Dict[str, Any]:
        """Set the current iframe source URL."""
        src = input.get("src")
        if not src:
            return {
                "success": False,
                "error": "Missing 'src' parameter"
            }
        
        with self._activity_lock:
            self._current_iframe_src = src
        
        # Add activity for iframe source change
        self._add_activity({
            "type": "iframe_change",
            "description": f"Iframe source changed to: {src}",
            "url": src
        })
        
        return {
            "success": True,
            "iframe_src": src
        }
    
    def _get_iframe_src(self) -> Dict[str, Any]:
        """Get the current iframe source URL."""
        with self._activity_lock:
            return {
                "success": True,
                "iframe_src": self._current_iframe_src
            }
    
    def _clear_activities(self) -> Dict[str, Any]:
        """Clear all stored activities."""
        with self._activity_lock:
            self._activities.clear()
        
        return {
            "success": True,
            "message": "All activities cleared"
        }
    
    @classmethod
    def log_browser_activity(cls, action: str, url: str, description: str = "", data: Dict[str, Any] = None):
        """Helper method to log browser activities from other parts of the application."""
        activity = {
            "type": "browser",
            "description": description or f"Browser {action}: {url}",
            "url": url,
            "data": data or {"action": action}
        }
        
        with cls._activity_lock:
            cls._activities.append({
                "id": f"activity_{int(time.time() * 1000)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **activity
            })
            
            # Keep only the most recent activities
            if len(cls._activities) > cls._max_activities:
                cls._activities = cls._activities[-cls._max_activities:]
    
    @classmethod
    def log_coding_activity(cls, action: str, file_path: str, description: str = "", data: Dict[str, Any] = None):
        """Helper method to log coding activities from other parts of the application."""
        activity = {
            "type": "coding",
            "description": description or f"Code {action}: {file_path}",
            "url": file_path,
            "data": data or {"action": action, "file": file_path}
        }
        
        with cls._activity_lock:
            cls._activities.append({
                "id": f"activity_{int(time.time() * 1000)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **activity
            })
            
            # Keep only the most recent activities
            if len(cls._activities) > cls._max_activities:
                cls._activities = cls._activities[-cls._max_activities:]