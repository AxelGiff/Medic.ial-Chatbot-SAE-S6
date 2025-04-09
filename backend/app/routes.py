from fastapi import APIRouter
import json
import os
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from app.services import *

import os

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "bienvenue"}


@router.post("/register")
def register_user(data: User):
    
    if does_user_exist(data.email) == None:
        try :
            insert_user(data)
            return {"message" : f"Bonjour {data.prenom}"}
        except: 
            print("L'insertion a echoué")
            
    return {"message" : "Utilisateur déjà existant"}
   
@router.get("/users")
def get_users():
    return get_all_user()