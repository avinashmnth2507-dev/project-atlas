"""
Home API endpoint.
"""

from flask import Blueprint, jsonify

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def home():
    """
    Home endpoint.
    """

    return jsonify(
        {
            "message": "Welcome to Project Atlas!",
            "application": "Project Atlas",
            "status": "running",
        }
    )