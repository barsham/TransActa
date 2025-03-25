import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create a Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)

# Configure the application
app.secret_key = os.environ.get("SESSION_SECRET")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///sillypostilion.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with SQLAlchemy
db.init_app(app)

# Import routes
from routes import register_routes

# Register all routes with the app
register_routes(app)

# Create database tables
with app.app_context():
    # Import models
    import models
    
    # Create all tables
    db.create_all()
    
    app.logger.info("Database tables created")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
