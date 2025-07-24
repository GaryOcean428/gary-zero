"""Calendar integration plugin for Gary-Zero."""

from datetime import datetime

from framework.helpers.tool import Response, Tool


class CalendarIntegration(Tool):
    """Calendar integration tool for scheduling and event management."""

    async def execute(self, **kwargs) -> Response:
        """Execute calendar operations."""

        action = self.args.get("action", "").lower()

        if action == "create_event":
            return await self._create_event()
        elif action == "list_events":
            return await self._list_events()
        elif action == "find_free_time":
            return await self._find_free_time()
        else:
            return Response(
                message=f"Unknown calendar action: {action}. Available actions: create_event, list_events, find_free_time",
                break_loop=False,
            )

    async def _create_event(self) -> Response:
        """Create a calendar event."""
        title = self.args.get("title", "New Event")
        start_time = self.args.get("start_time", "")
        duration = int(self.args.get("duration", 60))  # minutes
        description = self.args.get("description", "")

        # Mock calendar event creation
        event = {
            "id": f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "start_time": start_time,
            "duration": duration,
            "description": description,
            "created_at": datetime.now().isoformat(),
        }

        return Response(
            message=f"✅ Calendar event created: '{title}' at {start_time} for {duration} minutes\nEvent ID: {event['id']}",
            break_loop=False,
        )

    async def _list_events(self) -> Response:
        """List calendar events."""
        date = self.args.get("date", datetime.now().strftime("%Y-%m-%d"))

        # Mock events for demonstration
        mock_events = [
            {"title": "Team Meeting", "time": "09:00", "duration": 60},
            {"title": "Code Review", "time": "14:30", "duration": 30},
            {"title": "Project Planning", "time": "16:00", "duration": 90},
        ]

        events_text = f"📅 Events for {date}:\n"
        for i, event in enumerate(mock_events, 1):
            events_text += (
                f"{i}. {event['title']} at {event['time']} ({event['duration']} min)\n"
            )

        return Response(message=events_text, break_loop=False)

    async def _find_free_time(self) -> Response:
        """Find free time slots."""
        date = self.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        duration = int(self.args.get("duration", 60))  # minutes

        # Mock free time slots
        free_slots = ["10:00-11:00", "12:00-13:00", "15:00-16:00"]

        slots_text = f"🆓 Available {duration}-minute slots on {date}:\n"
        for i, slot in enumerate(free_slots, 1):
            slots_text += f"{i}. {slot}\n"

        return Response(message=slots_text, break_loop=False)
