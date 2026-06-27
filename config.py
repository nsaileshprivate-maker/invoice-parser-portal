"""
Configuration file for Invoice & Shipment Bill Parser Portal
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask settings
    DEBUG = False
    TESTING = False
    PROPAGATE_EXCEPTIONS = True
    
    # Database
    DATABASE = 'parser.db'
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True for HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS settings
    CORS_ORIGINS = ['*']  # Restrict in production
    
    # Logging
    LOG_FILE = 'parser.log'
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    CORS_ORIGINS = ['your-domain.com']  # Restrict to your domain

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE = 'test.db'
    WTF_CSRF_ENABLED = False

# Configuration selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
