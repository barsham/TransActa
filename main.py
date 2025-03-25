import sys
import os

# Add the web-portal directory to Python's module search path
sys.path.append(os.path.join(os.path.dirname(__file__), 'web-portal'))

# Import the app from the web-portal module
from app import app

# This is used by gunicorn to run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)