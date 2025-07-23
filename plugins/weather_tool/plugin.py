"""Weather tool plugin for Gary-Zero."""

from datetime import datetime

from framework.helpers.tool import Response, Tool
BaseClass = Tool


class WeatherTool(BaseClass):
    """Weather information tool."""

    async def execute(self, **kwargs) -> Response:
        """Execute weather operations."""

        action = self.args.get("action", "current").lower()

        if action == "current":
            return await self._get_current_weather()
        elif action == "forecast":
            return await self._get_forecast()
        elif action == "alerts":
            return await self._get_alerts()
        else:
            return Response(
                message=f"Unknown weather action: {action}. Available: current, forecast, alerts",
                break_loop=False
            )

    async def _get_current_weather(self) -> Response:
        """Get current weather conditions."""
        location = self.args.get("location", "New York, NY")

        # Mock weather data
        weather = {
            "location": location,
            "temperature": "22°C",
            "condition": "Partly Cloudy",
            "humidity": "65%",
            "wind": "15 km/h NW",
            "pressure": "1013 hPa",
            "visibility": "10 km",
            "updated": datetime.now().strftime("%H:%M")
        }

        response = f"🌤️ Current Weather for {location}:\n"
        response += f"🌡️ Temperature: {weather['temperature']}\n"
        response += f"☁️ Condition: {weather['condition']}\n"
        response += f"💧 Humidity: {weather['humidity']}\n"
        response += f"💨 Wind: {weather['wind']}\n"
        response += f"📊 Pressure: {weather['pressure']}\n"
        response += f"👁️ Visibility: {weather['visibility']}\n"
        response += f"🕒 Updated: {weather['updated']}"

        return Response(message=response, break_loop=False)

    async def _get_forecast(self) -> Response:
        """Get weather forecast."""
        location = self.args.get("location", "New York, NY")
        days = int(self.args.get("days", 3))

        # Mock forecast data
        forecast_days = [
            {"day": "Today", "high": "25°C", "low": "18°C", "condition": "Sunny", "icon": "☀️"},
            {"day": "Tomorrow", "high": "23°C", "low": "16°C", "condition": "Cloudy", "icon": "☁️"},
            {"day": "Day 3", "high": "20°C", "low": "14°C", "condition": "Rainy", "icon": "🌧️"},
            {"day": "Day 4", "high": "22°C", "low": "15°C", "condition": "Partly Cloudy", "icon": "⛅"},
            {"day": "Day 5", "high": "24°C", "low": "17°C", "condition": "Sunny", "icon": "☀️"}
        ]

        response = f"📅 {days}-Day Forecast for {location}:\n\n"

        for i, day in enumerate(forecast_days[:days]):
            response += f"{day['icon']} {day['day']}: {day['condition']}\n"
            response += f"   High: {day['high']}, Low: {day['low']}\n\n"

        return Response(message=response.strip(), break_loop=False)

    async def _get_alerts(self) -> Response:
        """Get weather alerts."""
        location = self.args.get("location", "New York, NY")

        # Mock alerts
        alerts = [
            {
                "type": "Advisory",
                "title": "High Wind Advisory",
                "description": "Winds up to 50 km/h expected",
                "severity": "Minor",
                "icon": "💨"
            }
        ]

        if not alerts:
            return Response(
                message=f"🟢 No weather alerts for {location}",
                break_loop=False
            )

        response = f"⚠️ Weather Alerts for {location}:\n\n"

        for alert in alerts:
            response += f"{alert['icon']} {alert['type']}: {alert['title']}\n"
            response += f"   {alert['description']}\n"
            response += f"   Severity: {alert['severity']}\n\n"

        return Response(message=response.strip(), break_loop=False)
