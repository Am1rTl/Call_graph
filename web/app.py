from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from routes import setup_routes  # Import route setup
from models import db  # Import the db object
# Initialize Flask application
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key

# Initialize SQLAlchemy
db.init_app(app)  # Pass the app to db.init_app

# Setup routes
setup_routes(app)

# Create database tables within the application context
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
