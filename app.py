"""WSGI entry point for the gary-zero Flask application."""

from run_ui import webapp

# Export the Flask app for gunicorn
app = webapp

if __name__ == "__main__":
    app.run()
