import os
from flask import Flask
from flask_cors import CORS
from routes import api


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    CORS(app, origins=os.getenv("CORS_ORIGINS", "*").split(","), supports_credentials=True)
    app.register_blueprint(api)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
