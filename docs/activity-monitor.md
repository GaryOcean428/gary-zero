# Live Activity Monitor

The Live Activity Monitor provides real-time tracking of browser activities, coding operations, and user interactions within the Gary-Zero application.

## Features

### 🔄 Real-Time Monitoring

- Automatic activity tracking for browser navigation, code editing, and iframe changes
- Updates every 3 seconds with smooth animations
- Activity count indicators and notifications

### 🎛️ Interactive Controls

- **Toggle Visibility**: Collapsible interface with activity count badge
- **Filter Activities**: View all activities or filter by type (Browser, Coding, Iframe Changes)
- **Refresh**: Manual refresh of activity data
- **Load External URLs**: Load any URL in the activity monitor iframe
- **Clear Activities**: Remove all stored activities

### 🎨 Modern UI Design

- Beautiful glassmorphism design with gradient backgrounds
- Responsive layout that works on desktop and mobile
- Smooth animations and transitions
- Dark mode compatible styling

## Usage

### Accessing the Activity Monitor

1. **Main UI Integration**: Look for the "📺 Live Activity Monitor" section in the main interface
2. **Click to Toggle**: Click the toggle button to expand/collapse the monitor
3. **Activity Counter**: The badge shows the current number of activities

### Activity Types

- **Browser**: Web navigation, API calls, external resource access
- **Coding**: File operations, AI interactions, settings changes
- **Iframe Changes**: Activity monitor iframe source modifications

### API Endpoints

The activity monitor is powered by the `/activity_monitor` API endpoint:

```javascript
// Get current status
fetch('/activity_monitor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'get_status' })
});

// Get recent activities
fetch('/activity_monitor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        action: 'get_activities',
        limit: 50,
        type: 'browser' // optional filter
    })
});

// Add a new activity
fetch('/activity_monitor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        action: 'add_activity',
        type: 'coding',
        description: 'User edited file',
        url: 'path/to/file.js',
        data: { action: 'edit', lines: 42 }
    })
});
```

### Programmatic Usage

The activity monitor can be controlled programmatically via the global `window.activityMonitor` object:

```javascript
// Log a custom activity
window.activityMonitor.logActivity(
    'browser',
    'User performed custom action',
    'https://example.com',
    { customData: 'value' }
);

// Get recent activities
const activities = await window.activityMonitor.getActivities(25, 'coding');

// Clear all activities
await window.activityMonitor.clearActivities();
```

## Integration Points

### Automatic Activity Logging

The system automatically logs activities for:

- **Message Sending**: When users send messages to the AI
- **AI Responses**: When the AI responds to user messages
- **Navigation**: Browser history changes and page navigation
- **Settings**: Configuration changes and API calls
- **Focus Changes**: When users switch between the app and other windows
- **External APIs**: Calls to external services and resources

### File Operations

File browser operations can be logged using:

```javascript
// Log file operations from anywhere in the application
window.logCodingActivity('upload', 'path/to/file.txt', 'User uploaded new file');
window.logCodingActivity('delete', 'old/file.js', 'User deleted obsolete file');
```

## Testing

### Test Page

Visit `/activity-monitor-test.html` for a standalone test interface with:
- Direct iframe embedding
- API connection testing
- Sample data population
- Activity manipulation controls

### Sample Data

Use the "Populate Sample Data" feature to add realistic test activities for development and demonstration purposes.

## Configuration

### Activity Limits

- Maximum stored activities: 100 (configurable via `_max_activities`)
- Auto-refresh interval: 3 seconds
- Activity retention: In-memory only (cleared on server restart)

### Responsive Design

The activity monitor automatically adapts to different screen sizes:
- **Desktop**: Full feature set with side-by-side controls
- **Tablet**: Stacked layout with preserved functionality
- **Mobile**: Simplified controls and compressed iframe height

## Security

- Activities are stored in-memory only
- API endpoints require authentication
- iframe uses sandbox restrictions for security
- External URL loading requires user confirmation

## Browser Compatibility

- Modern browsers with ES6+ support
- Alpine.js compatibility
- CSS Grid and Flexbox support
- Fetch API availability

---

The Live Activity Monitor enhances the Gary-Zero development experience by providing real-time visibility into system activities and user interactions, making debugging and monitoring significantly easier.
