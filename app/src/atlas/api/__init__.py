"""
API Blueprint exports.
"""

from atlas.api.health import health_bp
from atlas.api.home import home_bp
from atlas.api.info import info_bp
from atlas.api.version import version_bp

__all__ = [
    "health_bp",
    "home_bp",
    "info_bp",
    "version_bp",
]