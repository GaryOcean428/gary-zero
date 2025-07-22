"""
Sample activity data for testing the activity monitor
This can be used to populate initial test data
"""

SAMPLE_ACTIVITIES = [
    {
        "type": "browser",
        "description": "User navigated to GitHub repository",
        "url": "https://github.com/GaryOcean428/gary-zero",
        "data": {"action": "navigate", "referrer": "search"}
    },
    {
        "type": "coding",
        "description": "Opened file for editing: activity_monitor.py",
        "url": "framework/api/activity_monitor.py",
        "data": {"action": "open", "editor": "vscode"}
    },
    {
        "type": "browser",
        "description": "AI performed web search for 'Flask API best practices'",
        "url": "https://search.example.com/q=flask+api+best+practices",
        "data": {"action": "search", "query": "Flask API best practices"}
    },
    {
        "type": "coding",
        "description": "Created new JavaScript file: activity-monitor.js",
        "url": "webui/js/activity-monitor.js",
        "data": {"action": "create", "fileSize": 10748}
    },
    {
        "type": "iframe_change",
        "description": "Activity monitor iframe source changed to activity viewer",
        "url": "./activity-monitor.html",
        "data": {"previousSrc": "about:blank"}
    },
    {
        "type": "browser",
        "description": "Agent accessed external API: OpenAI GPT-4",
        "url": "https://api.openai.com/v1/chat/completions",
        "data": {"action": "api_call", "model": "gpt-4", "tokens": 1500}
    },
    {
        "type": "coding",
        "description": "Modified CSS file to add activity monitor styles",
        "url": "webui/index.css",
        "data": {"action": "modify", "linesAdded": 150}
    }
]

def get_sample_activities():
    """Return a copy of sample activities with timestamps"""
    import datetime
    import random

    activities = []
    base_time = datetime.datetime.now(datetime.UTC)

    for i, activity in enumerate(SAMPLE_ACTIVITIES):
        # Create activities with timestamps going back in time
        timestamp = base_time - datetime.timedelta(minutes=random.randint(1, 60))

        activity_with_timestamp = {
            "id": f"sample_activity_{i}",
            "timestamp": timestamp.isoformat(),
            **activity
        }
        activities.append(activity_with_timestamp)

    return activities
