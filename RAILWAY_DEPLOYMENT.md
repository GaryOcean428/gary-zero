# Railway Deployment Configuration

This document explains the Railway deployment configuration for the gary-zero project.

## Configuration Files

### nixpacks.toml
Explicitly specifies Python 3.12 as the provider to prevent Railway from misidentifying the project as Node.js due to the presence of `package-lock.json`.

```toml
[providers]
python = "3.12"
```

### Procfile
Defines how Railway should start the web application using Gunicorn as the WSGI server.

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### app.py
Simple WSGI entry point that imports the Flask application from `run_ui.py` and exports it for Gunicorn.

```python
from run_ui import webapp
app = webapp
```

### requirements.txt
Updated to include `gunicorn==23.0.0` for production deployment.

### railway.toml
Updated build command to focus on Python dependencies only:

```toml
buildCommand = "pip install -r requirements.txt"
```

## Issues Resolved

1. **Missing Procfile**: Added Procfile to specify application startup command
2. **Incorrect Project Detection**: Added nixpacks.toml to explicitly specify Python provider
3. **Missing Gunicorn**: Added gunicorn to requirements.txt for production WSGI server

## Deployment Process

1. Railway detects Python project due to nixpacks.toml
2. Railway runs `pip install -r requirements.txt` to install dependencies including gunicorn
3. Railway starts the application using the Procfile command: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Gunicorn imports the Flask app from app.py and serves it on the Railway-provided port

## Testing Locally

To test the configuration locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Start with gunicorn (similar to Railway)
gunicorn app:app --bind 127.0.0.1:8000

# Or run the development server
python run_ui.py
```