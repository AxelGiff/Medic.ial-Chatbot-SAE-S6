from fastapi import APIRouter
import json
import os
from pydantic import BaseModel, EmailStr
import hashlib
from pymongo import MongoClient

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]

router = APIRouter()


class RegisterData(BaseModel):
     prenom:str
     nom:str
     email:EmailStr
     password:str


@router.get("/")
def read_root():
    return {"message": "bienvenue"}


@router.post("/register")
def register_user(data: RegisterData):
   password_hash = hashlib.sha256(data.password.encode('utf-8')).hexdigest()
   user_data={
        "message": "utilisateur reçu",
        "prenom": data.prenom,
        "nom": data.nom,
        "email": data.email,
        "password_hash": password_hash
    }
   result = users_collection.insert_one(user_data)
   return {
        "message": "utilisateur enregistré",
        "prenom": data.prenom,
        "nom": data.nom,
        "email": data.email,
        "password_hash": password_hash,
        "user_id": str(result.inserted_id)
    }
