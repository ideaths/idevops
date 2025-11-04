from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])  # simple readiness/liveness endpoint
    def health():
        return jsonify({"status": "ok"}), 200

    return app