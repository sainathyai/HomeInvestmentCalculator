from flask import Blueprint, render_template, request, jsonify
from .engine import calculate

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    try:
        result = calculate(data)
        return jsonify(result)
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 422
