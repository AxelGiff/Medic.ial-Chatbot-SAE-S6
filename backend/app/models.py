from pydantic import BaseModel
from pydantic import EmailStr


class User(BaseModel):
    prenom: str
    nom: str
    email: EmailStr
    password: str