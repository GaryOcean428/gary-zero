"""Slack notifier plugin for Gary-Zero."""

from datetime import datetime

from framework.helpers.tool import Response, Tool


class SlackNotifier(Tool):
    """Slack integration tool for sending messages and notifications."""

    async def execute(self, **kwargs) -> Response:
        """Execute Slack operations."""

        action = self.args.get("action", "").lower()

        if action == "send_message":
            return await self._send_message()
        elif action == "send_notification":
            return await self._send_notification()
        elif action == "list_channels":
            return await self._list_channels()
        else:
            return Response(
                message=f"Unknown Slack action: {action}. Available actions: send_message, send_notification, list_channels",
                break_loop=False
            )

    async def _send_message(self) -> Response:
        """Send a message to a Slack channel."""
        channel = self.args.get("channel", "#general")
        message = self.args.get("message", "")

        if not message:
            return Response(
                message="❌ Message content is required",
                break_loop=False
            )

        # Mock Slack message sending
        timestamp = datetime.now().strftime("%H:%M:%S")

        return Response(
            message=f"💬 Message sent to {channel} at {timestamp}:\n'{message}'",
            break_loop=False
        )

    async def _send_notification(self) -> Response:
        """Send a notification to Slack."""
        recipient = self.args.get("recipient", "@channel")
        title = self.args.get("title", "Notification")
        message = self.args.get("message", "")
        priority = self.args.get("priority", "normal").lower()

        priority_emoji = {
            "low": "ℹ️",
            "normal": "📢",
            "high": "⚠️",
            "urgent": "🚨"
        }.get(priority, "📢")

        return Response(
            message=f"{priority_emoji} Notification sent to {recipient}:\n**{title}**\n{message}",
            break_loop=False
        )

    async def _list_channels(self) -> Response:
        """List available Slack channels."""
        # Mock channel list
        channels = [
            "#general",
            "#development",
            "#ai-agents",
            "#notifications",
            "#random"
        ]

        channels_text = "📋 Available Slack channels:\n"
        for i, channel in enumerate(channels, 1):
            channels_text += f"{i}. {channel}\n"

        return Response(
            message=channels_text,
            break_loop=False
        )
