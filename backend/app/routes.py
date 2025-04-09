from fastapi import APIRouter
import json
import os
from pydantic import BaseModel, EmailStr

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
   return {
        "message": "utilisateur reçu",
        "prenom": data.prenom,
        "nom": data.nom,
        "email": data.email,
        "password_hash": data.password
    }