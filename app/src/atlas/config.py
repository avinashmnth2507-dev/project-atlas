"""
Application configuration for Project Atlas.
"""

import os


class Config:
    """Base configuration."""

    APP_NAME = "Project Atlas"
    VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("FLASK_ENV", "development")
    DEBUG = ENVIRONMENT == "development"