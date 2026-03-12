import os
from pymongo import MongoClient


def get_database():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/url_shortener")
    client = MongoClient(mongo_uri)
    db_name = os.getenv("MONGO_DB_NAME", "url_shortener")
    return client[db_name]


db = get_database()
users_collection = db["users"]
links_collection = db["links"]
clicks_collection = db["clicks"]

# Useful indexes
users_collection.create_index("email", unique=True)
users_collection.create_index("username", unique=True)
links_collection.create_index("short_code", unique=True)
links_collection.create_index("user_id")
clicks_collection.create_index("link_id")
