"""
Version API endpoint.
"""

from flask import Blueprint, jsonify

from atlas.config import Config

version_bp = Blueprint("version", __name__)


@version_bp.route("/version", methods=["GET"])
def version():
    """
    Application version.
    """

    return jsonify(
        {
            "version": Config.VERSION
        }
    )