from flask import Blueprint, jsonify

map_bp = Blueprint("map", __name__)

@map_bp.route("/api/map/spots")
def map_spots():
    return jsonify({
        "ok": True,
        "spots": [],
        "count": 0,
        "last": None
    })

