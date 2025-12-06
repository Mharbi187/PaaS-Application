"""
Main Flask application for PaaS Platform
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from pathlib import Path
from config import config, Config

# Import backend modules
from backend.api.routes import api_bp
from backend.utils.helpers import setup_logging
from backend.extensions import db, migrate, init_extensions

def create_app(config_name='default'):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration to use (development, production, testing)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize app directories
    Config.init_app()
    
    # Setup logging
    setup_logging(app.config['LOG_FILE'], app.config['LOG_LEVEL'])
    
    # Enable CORS
    CORS(app)
    
    # Initialize extensions (database, migrations)
    init_extensions(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Routes
    @app.route('/')
    def index():
        """Main page"""
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/deploy')
    def deploy():
        """Deployment page"""
        return render_template('deployment.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'PaaS Platform',
            'version': '1.0.0'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    # Create app instance
    app = create_app('development')
    
    # Run the application
    app.run(
        host=app.config['APP_HOST'],
        port=app.config['APP_PORT'],
        debug=app.config['DEBUG'],
        use_reloader=False  # Disable auto-reloader
    )
