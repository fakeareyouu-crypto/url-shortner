import random
import string
from datetime import datetime, timezone
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from database import users_collection, links_collection, clicks_collection


def utc_now():
    return datetime.now(timezone.utc)


def object_id(value: str):
    return ObjectId(value)


def serialize_id(document):
    if not document:
        return None
    document["id"] = str(document.pop("_id"))
    return document


def generate_short_code(length=6):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def create_user(username, email, password, is_admin=False):
    payload = {
        "username": username,
        "email": email.lower(),
        "password": generate_password_hash(password),
        "is_admin": is_admin,
        "created_at": utc_now(),
    }
    result = users_collection.insert_one(payload)
    payload["_id"] = result.inserted_id
    return serialize_id(payload)


def find_user_by_email(email):
    return users_collection.find_one({"email": email.lower()})


def find_user_by_id(user_id):
    return users_collection.find_one({"_id": object_id(user_id)})


def verify_password(user, password):
    return check_password_hash(user["password"], password)


def create_link(user_id, original_url, custom_alias=None, expires_at=None):
    short_code = custom_alias or generate_short_code(6)
    while links_collection.find_one({"short_code": short_code}):
        short_code = generate_short_code(6)

    payload = {
        "user_id": object_id(user_id),
        "original_url": original_url,
        "short_code": short_code,
        "clicks": 0,
        "created_at": utc_now(),
        "expires_at": expires_at,
    }
    result = links_collection.insert_one(payload)
    payload["_id"] = result.inserted_id
    return serialize_id(payload)


def find_link_by_short_code(short_code):
    return links_collection.find_one({"short_code": short_code})


def user_links(user_id):
    docs = links_collection.find({"user_id": object_id(user_id)}).sort("created_at", -1)
    return [serialize_id(doc) for doc in docs]


def delete_link(user_id, link_id):
    return links_collection.delete_one({"_id": object_id(link_id), "user_id": object_id(user_id)})


def register_click(link_id, ip_address, country=None):
    clicks_collection.insert_one(
        {
            "link_id": object_id(link_id),
            "ip_address": ip_address,
            "country": country,
            "timestamp": utc_now(),
        }
    )
    links_collection.update_one({"_id": object_id(link_id)}, {"$inc": {"clicks": 1}})


def dashboard_stats(user_id):
    links = user_links(user_id)
    total_clicks = sum(link.get("clicks", 0) for link in links)
    return {"links": links, "total_links": len(links), "total_clicks": total_clicks}


def admin_stats():
    total_users = users_collection.count_documents({})
    total_links = links_collection.count_documents({})
    total_clicks = clicks_collection.count_documents({})
    top_links = list(links_collection.find().sort("clicks", -1).limit(10))
    top_links = [serialize_id(doc) for doc in top_links]
    return {
        "total_users": total_users,
        "total_links": total_links,
        "total_clicks": total_clicks,
        "top_links": top_links,
    }
