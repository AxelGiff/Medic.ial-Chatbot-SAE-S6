import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME")]
    print(db)
except Exception as e:
    print("Erreur de connexion :", e)
