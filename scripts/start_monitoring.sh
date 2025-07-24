#!/bin/bash

# 24-Hour Log Monitoring Management Script
# Starts and manages the 24-hour log monitoring process for Gary-Zero production

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/log_monitor_24h.py"
PID_FILE="$SCRIPT_DIR/monitor.pid"
LOG_FILE="$SCRIPT_DIR/monitor_output.log"

case "${1:-start}" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "⚠️  Monitoring is already running (PID: $(cat "$PID_FILE"))"
            echo "Use '$0 status' to check or '$0 stop' to stop"
            exit 1
        fi

        echo "🚀 Starting 24-hour log monitoring for Gary-Zero production..."
        echo "📁 Monitor output will be logged to: $LOG_FILE"
        echo "🔧 Process ID will be saved to: $PID_FILE"

        # Start monitoring in background (unbuffered output)
        nohup python3 -u "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
        MONITOR_PID=$!
        echo $MONITOR_PID > "$PID_FILE"

        echo "✅ Monitoring started with PID: $MONITOR_PID"
        echo ""
        echo "📋 Management commands:"
        echo "  $0 status   - Check monitoring status"
        echo "  $0 stop     - Stop monitoring"
        echo "  $0 logs     - View recent monitoring output"
        echo "  $0 tail     - Follow monitoring output in real-time"
        echo ""
        echo "⏰ Monitoring will run for 24 hours and generate a final report"
        ;;

    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ No monitoring process found (no PID file)"
            exit 1
        fi

        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 Stopping monitoring process (PID: $PID)..."
            kill "$PID"
            sleep 2

            if kill -0 "$PID" 2>/dev/null; then
                echo "⚠️  Process still running, force killing..."
                kill -9 "$PID"
            fi

            rm -f "$PID_FILE"
            echo "✅ Monitoring stopped"
        else
            echo "❌ Process not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
        ;;

    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            PID=$(cat "$PID_FILE")
            echo "✅ Monitoring is RUNNING (PID: $PID)"

            # Show process info
            echo ""
            echo "📊 Process Information:"
            ps -p "$PID" -o pid,ppid,cmd,etime,time

            # Show recent activity from log
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "📝 Recent Activity (last 10 lines):"
                tail -n 10 "$LOG_FILE"
            fi
        else
            echo "❌ Monitoring is NOT RUNNING"
            if [ -f "$PID_FILE" ]; then
                echo "🗑️  Cleaning up stale PID file"
                rm -f "$PID_FILE"
            fi
        fi
        ;;

    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📄 Monitoring Output Log:"
            echo "========================"
            cat "$LOG_FILE"
        else
            echo "❌ No log file found at: $LOG_FILE"
        fi
        ;;

    tail)
        if [ -f "$LOG_FILE" ]; then
            echo "📡 Following monitoring output (Ctrl+C to exit):"
            echo "================================================"
            tail -f "$LOG_FILE"
        else
            echo "❌ No log file found at: $LOG_FILE"
            echo "💡 Start monitoring first with: $0 start"
        fi
        ;;

    *)
        echo "Gary-Zero 24-Hour Log Monitoring Manager"
        echo "========================================"
        echo ""
        echo "Usage: $0 {start|stop|status|logs|tail}"
        echo ""
        echo "Commands:"
        echo "  start   - Start 24-hour monitoring process in background"
        echo "  stop    - Stop monitoring process"
        echo "  status  - Check if monitoring is running and show recent activity"
        echo "  logs    - Display complete monitoring output log"
        echo "  tail    - Follow monitoring output in real-time"
        echo ""
        echo "The monitoring process will:"
        echo "• Check Railway logs every 5 minutes for 24 hours"
        echo "• Alert on 4xx/5xx HTTP error spikes"
        echo "• Generate a comprehensive report when complete"
        echo "• Save all output to monitor_output.log"
        ;;
esac
