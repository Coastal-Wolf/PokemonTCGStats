#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Configuration
Centralized configuration management for the application.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pokemon-tcg-tracker-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Data Storage Configuration
    DATA_FILE = os.environ.get('DATA_FILE') or 'data/user_data.py'
    BACKUP_DIR = os.environ.get('BACKUP_DIR') or 'data/backups'
    
    # Auto-save Configuration
    AUTO_SAVE_INTERVAL = int(os.environ.get('AUTO_SAVE_INTERVAL', 30))  # seconds
    AUTO_BACKUP_INTERVAL = int(os.environ.get('AUTO_BACKUP_INTERVAL', 24))  # hours
    MAX_BACKUPS = int(os.environ.get('MAX_BACKUPS', 7))  # number of backups to keep
    
    # API Configuration
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '100 per minute')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # Database Configuration (if you want to switch to SQLite later)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///pokemon_tcg.db'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/pokemon_tcg.log'
    
    # Application Information
    APP_NAME = 'Pokemon TCG Tracker'
    APP_VERSION = '2.1.0'
    APP_DESCRIPTION = 'Professional Pokemon TCG match tracking with advanced analytics'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config."""
        # Create necessary directories
        os.makedirs(os.path.dirname(Config.DATA_FILE), exist_ok=True)
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    AUTO_SAVE_INTERVAL = 10  # More frequent saves in development
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    AUTO_SAVE_INTERVAL = 60  # Less frequent saves in production
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set up file logging in production
        if not app.debug and not app.testing:
            file_handler = RotatingFileHandler(
                cls.LOG_FILE,
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info(f'{cls.APP_NAME} startup')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    DATA_FILE = 'data/test_user_data.py'
    AUTO_SAVE_INTERVAL = 1  # Very frequent saves for testing


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get the appropriate configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])