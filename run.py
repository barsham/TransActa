#!/usr/bin/env python3

import os
import sys
import subprocess

def main():
    """
    Main entry point for running the web portal application
    """
    # Change to the web-portal directory
    os.chdir('web-portal')
    
    # Run the Flask application
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()