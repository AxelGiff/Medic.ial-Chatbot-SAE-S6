from app.config import db
from app.models import *
import hashlib

def get_all_user():
    return list(db.users.find({}, {'_id': 0}))

def does_user_exist(email):
    res = db.users.find_one({"email": email})
    return res

def insert_user(data: User):
    print("Dans insert")
    password_hash = hashlib.sha256(data.password.encode('utf-8')).hexdigest()
    user_data={
            "message": "utilisateur reçu",
            "prenom": data.prenom,
            "nom": data.nom,
            "email": data.email,
            "password_hash": password_hash
        }
    result = db.users.insert_one(user_data)
    return {
            "message": "utilisateur enregistré",
            "prenom": data.prenom,
            "nom": data.nom,
            "email": data.email,
            "password_hash": password_hash,
            "user_id": str(result.inserted_id)
    }