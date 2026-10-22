"""
Health check endpoint.
"""

from flask import Blueprint, jsonify

from atlas.config import Config

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    """
    return jsonify(
        {
            "status": "healthy",
            "application": "Project Atlas",
            "version": Config.VERSION,
        }
    )
