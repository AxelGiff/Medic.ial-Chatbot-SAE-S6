from fastapi import APIRouter, Request, Response, HTTPException, Depends
from datetime import datetime, timedelta
from passlib.hash import bcrypt
import secrets
from bson.objectid import ObjectId

from database import get_db

router = APIRouter(prefix="/api", tags=["Authentification"])

# Fonction pour inscrire un utilisateur dans la base MongoDB
@router.post("/register")
async def register(request: Request):
    data = await request.json()
    db = get_db()
    
    required_fields = ["prenom", "nom", "email", "password"]
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Le champ {field} est requis")
        
    existing_user = db.users.find_one({"email": data["email"]})
    if existing_user:
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
        
    hashed_password = bcrypt.hash(data["password"]) # On hash le password avec bcrypt pour la sécurité
        
    user = {
        "prenom": data["prenom"],
        "nom": data["nom"],
        "email": data["email"],
        "password": hashed_password,
        "createdAt": datetime.utcnow(),
        "role": data.get("role", "user"),  

    }
        
    result = db.users.insert_one(user)
    
    return {"message": "Utilisateur créé avec succès", "userId": str(result.inserted_id)}

# Fonction pour se connecter en tant qu'utilisateur ou admin
@router.post("/login")
async def login(request: Request, response: Response):
    try:
        data = await request.json()
        db = get_db()
        email = data.get("email")
        password = data.get("password")
        
        user = db.users.find_one({"email": email})
        if not user or not bcrypt.verify(password, user["password"]):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        session_id = secrets.token_hex(16)
        user_id = str(user["_id"])
        username = f"{user['prenom']} {user['nom']}"

        db.sessions.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        })

        response.set_cookie(
            key="session_id", 
            value=session_id, 
            httponly=False,  
            max_age=7*24*60*60,  
            samesite="none", 
            secure=True,      
            path="/"         
        )

        print(f"Session : {session_id} pour {user_id}")

        
        return {
            "success": True,
            "username": username,
            "user_id": user_id,
            "session_id": session_id,
            "role": user.get("role", "user")
        }
    except Exception as e:
        print(f"Erreur login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Fonction pour se déconnecter
@router.post("/logout")
async def logout(request: Request, response: Response):
    db = get_db()
    session_id = request.cookies.get("session_id")
    
    if session_id:
        db.sessions.delete_one({"session_id": session_id})
    
    response.delete_cookie(key="session_id")
    return {"success": True}

# Fonction pour activer les sessions
async def get_current_user(request: Request):
    db = get_db()
    session_id = request.cookies.get("session_id")
    
    print(f"Cookie: {session_id[:5] if session_id else 'None'}")
    
    if not session_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.replace("Bearer ", "")
            print(f"Session  reçue: {session_id[:5]}...")
    
    if not session_id:
        session_id = request.query_params.get("session_id")
        if session_id:
            print(f"Session des paramètres de requête: {session_id[:5]}...")
    
    if not session_id:
        raise HTTPException(status_code=401, detail="Non authentifié - Aucune session trouvée")
    
    session = db.sessions.find_one({
        "session_id": session_id,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expirée ou invalide")
    
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user

# fonction de middleware pour savoir si le role est administrateur ou non
async def get_admin_user(request: Request):
    user = await get_current_user(request)
    if user["role"] != "Administrateur":
        raise HTTPException(status_code=403, detail="Droits d'administrateur requis")
    return user
