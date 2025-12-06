"""
Database extensions initialization
Initializes SQLAlchemy and other Flask extensions
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def init_extensions(app):
    """
    Initialize Flask extensions
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    migrate.init_app(app, db)
