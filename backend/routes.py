import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, jsonify, request, render_template
from bson.errors import InvalidId
import jwt
import qrcode
import io
import base64
from models import (
    create_user,
    find_user_by_email,
    verify_password,
    create_link,
    find_link_by_short_code,
    register_click,
    dashboard_stats,
    delete_link,
    find_user_by_id,
    admin_stats,
)

api = Blueprint("api", __name__)


def _secret():
    return os.getenv("JWT_SECRET", "super-secret-change-me")


def create_token(user):
    payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "is_admin": user.get("is_admin", False),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def auth_required(admin=False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing token"}), 401
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, _secret(), algorithms=["HS256"])
                request.user_id = payload["sub"]
                request.is_admin = payload.get("is_admin", False)
            except jwt.PyJWTError:
                return jsonify({"error": "Invalid token"}), 401

            if admin and not request.is_admin:
                return jsonify({"error": "Admin access required"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@api.post("/api/signup")
def signup():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or len(password) < 6:
        return jsonify({"error": "Invalid signup payload"}), 400
    if find_user_by_email(email):
        return jsonify({"error": "Email already exists"}), 409

    user = create_user(username=username, email=email, password=password)
    return jsonify({"token": create_token({"_id": user["id"], "email": user["email"], "is_admin": False}), "user": user}), 201


@api.post("/api/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = find_user_by_email(email)
    if not user or not verify_password(user, password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"token": create_token(user), "user": {"id": str(user["_id"]), "username": user["username"], "email": user["email"], "is_admin": user.get("is_admin", False)}})


@api.post("/api/logout")
def logout():
    return jsonify({"message": "Logged out. Remove token on client."})


@api.post("/api/shorten")
@auth_required()
def shorten_url():
    data = request.get_json(force=True)
    original_url = data.get("original_url", "").strip()
    custom_alias = data.get("custom_alias", "").strip() or None
    expire_hours = data.get("expire_hours")

    if not (original_url.startswith("http://") or original_url.startswith("https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    expires_at = None
    if expire_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=float(expire_hours))

    link = create_link(request.user_id, original_url, custom_alias=custom_alias, expires_at=expires_at)
    base_url = os.getenv("PUBLIC_BASE_URL", request.host_url.rstrip("/"))
    short_url = f"{base_url}/r/{link['short_code']}"

    qr = qrcode.make(short_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    return jsonify({"link": link, "short_url": short_url, "qr_code": qr_data_url}), 201


@api.get("/api/dashboard")
@auth_required()
def dashboard():
    return jsonify(dashboard_stats(request.user_id))


@api.delete("/api/link/<link_id>")
@auth_required()
def delete_user_link(link_id):
    try:
        result = delete_link(request.user_id, link_id)
    except InvalidId:
        return jsonify({"error": "Invalid link id"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "Link not found"}), 404
    return jsonify({"message": "Link deleted"})


@api.get("/api/admin/stats")
@auth_required(admin=True)
def admin_dashboard():
    return jsonify(admin_stats())


@api.get("/r/<shortcode>")
def ad_redirect(shortcode):
    link = find_link_by_short_code(shortcode)
    if not link:
        return jsonify({"error": "Short link not found"}), 404

    expires_at = link.get("expires_at")
    if expires_at and datetime.now(timezone.utc) > expires_at:
        return jsonify({"error": "Short link expired"}), 410

    register_click(str(link["_id"]), request.headers.get("X-Forwarded-For", request.remote_addr), country=request.headers.get("CF-IPCountry"))
    return render_template("ad_redirect.html", original_url=link["original_url"], short_code=shortcode)
