"""
Health check endpoint.
"""

from flask import Blueprint, jsonify

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
            "version": "0.1.0",
        }
    )