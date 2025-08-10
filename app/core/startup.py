"""
Application startup validation and initialization
"""
import sys
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_configuration():
    """
    Validate critical configuration at application startup.
    This runs once when the application starts, not on every import.
    """
    errors = []
    
    # Check SECRET_KEY
    if not settings.SECRET_KEY:
        errors.append(
            "SECRET_KEY is not set. Please set it in .env file.\n"
            "Generate a secure key with: openssl rand -hex 32"
        )
    elif len(settings.SECRET_KEY) < 32:
        errors.append(
            f"SECRET_KEY is too short ({len(settings.SECRET_KEY)} chars). "
            "Minimum 32 characters required for security."
        )
    
    # Check DATABASE_URL
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is not configured")
    
    # Check CORS origins in production
    if not settings.DEBUG and not settings.cors_origins:
        logger.warning("No CORS origins configured for production")
    
    # If there are critical errors, exit
    if errors:
        logger.error("Configuration errors detected:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("Configuration validation passed")
    logger.info(f"Running {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")


def initialize_app():
    """
    Initialize application components.
    Called once at startup from main.py
    """
    # Validate configuration
    validate_configuration()
    
    # Future: Initialize database connections, cache, etc.
    pass