"""Application configuration settings."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/engineering_projects'
    )

    # Application environment: 'development' or 'production'
    ENV: str = os.environ.get('ENV', 'development')

    # Email (SMTP) settings – used when ENV != 'development' or OS is not Windows
    MAIL_SERVER: str = os.environ.get('MAIL_SERVER', '')
    MAIL_PORT: int = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS: bool = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME: str = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD: str = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER: str = os.environ.get('MAIL_DEFAULT_SENDER', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True
    LOG_LEVEL: str = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://engineering_user:password@localhost:5432/engineering_projects')
    WTF_CSRF_ENABLED: bool = False
    LOG_LEVEL: str = 'WARNING'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG: bool = False
    TESTING: bool = False
    LOG_LEVEL: str = 'INFO'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
