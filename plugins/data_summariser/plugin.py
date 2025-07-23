"""Data summariser plugin for Gary-Zero."""

import json

from framework.helpers.tool import Response, Tool


class DataSummariser(Tool):
    """Data analysis and summarization tool."""

    async def execute(self, **kwargs) -> Response:
        """Execute data summarization operations."""

        action = self.args.get("action", "").lower()

        if action == "summarize_list":
            return await self._summarize_list()
        elif action == "calculate_stats":
            return await self._calculate_stats()
        elif action == "analyze_trends":
            return await self._analyze_trends()
        else:
            return Response(
                message=f"Unknown data action: {action}. Available actions: summarize_list, calculate_stats, analyze_trends",
                break_loop=False
            )

    async def _summarize_list(self) -> Response:
        """Summarize a list of items."""
        data_str = self.args.get("data", "")

        try:
            if data_str.startswith('['):
                data = json.loads(data_str)
            else:
                data = data_str.split(',')
                data = [item.strip() for item in data]
        except:
            return Response(
                message="❌ Invalid data format. Please provide a JSON array or comma-separated values.",
                break_loop=False
            )

        if not data:
            return Response(
                message="❌ No data provided to summarize.",
                break_loop=False
            )

        summary = "📊 Data Summary:\n"
        summary += f"• Total items: {len(data)}\n"
        summary += f"• First item: {data[0]}\n"
        summary += f"• Last item: {data[-1]}\n"

        if len(data) > 5:
            summary += f"• Sample items: {', '.join(str(x) for x in data[:3])}...\n"
        else:
            summary += f"• All items: {', '.join(str(x) for x in data)}\n"

        return Response(
            message=summary,
            break_loop=False
        )

    async def _calculate_stats(self) -> Response:
        """Calculate basic statistics for numerical data."""
        data_str = self.args.get("data", "")

        try:
            if data_str.startswith('['):
                data = json.loads(data_str)
            else:
                data = [float(x.strip()) for x in data_str.split(',')]
        except:
            return Response(
                message="❌ Invalid numerical data format. Please provide numbers as JSON array or comma-separated values.",
                break_loop=False
            )

        if not data:
            return Response(
                message="❌ No numerical data provided.",
                break_loop=False
            )

        # Calculate statistics
        total = sum(data)
        count = len(data)
        mean = total / count
        minimum = min(data)
        maximum = max(data)

        # Calculate median
        sorted_data = sorted(data)
        if count % 2 == 0:
            median = (sorted_data[count//2 - 1] + sorted_data[count//2]) / 2
        else:
            median = sorted_data[count//2]

        stats = "📈 Statistical Summary:\n"
        stats += f"• Count: {count}\n"
        stats += f"• Sum: {total:.2f}\n"
        stats += f"• Mean: {mean:.2f}\n"
        stats += f"• Median: {median:.2f}\n"
        stats += f"• Min: {minimum:.2f}\n"
        stats += f"• Max: {maximum:.2f}\n"
        stats += f"• Range: {maximum - minimum:.2f}\n"

        return Response(
            message=stats,
            break_loop=False
        )

    async def _analyze_trends(self) -> Response:
        """Analyze trends in time-series data."""
        data_str = self.args.get("data", "")

        try:
            if data_str.startswith('['):
                data = json.loads(data_str)
            else:
                data = [float(x.strip()) for x in data_str.split(',')]
        except:
            return Response(
                message="❌ Invalid data format for trend analysis.",
                break_loop=False
            )

        if len(data) < 3:
            return Response(
                message="❌ Need at least 3 data points for trend analysis.",
                break_loop=False
            )

        # Simple trend analysis
        increases = 0
        decreases = 0

        for i in range(1, len(data)):
            if data[i] > data[i-1]:
                increases += 1
            elif data[i] < data[i-1]:
                decreases += 1

        trend = "📊 Trend Analysis:\n"
        trend += f"• Data points: {len(data)}\n"
        trend += f"• Increases: {increases}\n"
        trend += f"• Decreases: {decreases}\n"
        trend += f"• Stable: {len(data) - 1 - increases - decreases}\n"

        if increases > decreases:
            trend += "• Overall trend: 📈 Upward\n"
        elif decreases > increases:
            trend += "• Overall trend: 📉 Downward\n"
        else:
            trend += "• Overall trend: ➡️ Stable\n"

        # Calculate percentage change
        pct_change = ((data[-1] - data[0]) / data[0]) * 100
        trend += f"• Total change: {pct_change:.1f}%\n"

        return Response(
            message=trend,
            break_loop=False
        )
