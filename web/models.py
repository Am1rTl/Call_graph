from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Create a SQLAlchemy instance (without app initialization)

# Model for Users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    projects = db.relationship('Project', backref='owner', lazy=True)

# Model for Projects
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_content = db.Column(db.Text, nullable=False)
    window_state = db.Column(db.Text, nullable=True)  # JSON for window state
    created_at = db.Column(db.DateTime, server_default=db.func.now())
