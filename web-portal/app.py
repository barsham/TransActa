import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf.csrf import CSRFProtect
import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create a Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize CSRF protection
csrf = CSRFProtect()

# Create the Flask application
app = Flask(__name__)

# Configure the application
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")

# Security configuration
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in HTTPS environment
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(hours=24)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///sillypostilion.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with extensions
db.init_app(app)
csrf.init_app(app)

# Import routes
from routes import register_routes

# Import security manager
from security import security_manager

# Register all routes with the app
register_routes(app)

# Initialize security manager with app
security_manager.init_app(app)

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    headers = security_manager.secure_headers()
    for header, value in headers.items():
        response.headers[header] = value
    return response

# Create database tables
with app.app_context():
    # First check if we need to recreate tables
    try:
        # Import models
        import models
        
        # Try a simple query to see if our schema is up to date
        from models import Transaction, SystemStatus
        try:
            Transaction.query.first()
            SystemStatus.query.first()
            app.logger.info("Database schema appears to be up to date")
        except Exception as e:
            app.logger.warning(f"Database schema needs to be updated: {str(e)}")
            # Drop all tables
            app.logger.info("Dropping all tables to recreate schema")
            db.drop_all()
            
            # Create all tables with new schema
            app.logger.info("Creating tables with updated schema")
            db.create_all()
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        # Create all tables if they don't exist
        db.create_all()
    
    app.logger.info("Database initialization complete")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
