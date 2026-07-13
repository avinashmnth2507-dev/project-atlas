"""
Information API endpoint.
"""

from flask import Blueprint, jsonify

from atlas.config import Config

info_bp = Blueprint("info", __name__)


@info_bp.route("/info", methods=["GET"])
def info():
    """
    Application information.
    """

    return jsonify(
        {
            "application": Config.APP_NAME,
            "version": Config.VERSION,
            "environment": Config.ENVIRONMENT,
        }
    )