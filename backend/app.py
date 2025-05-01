from fastapi import FastAPI, Request, HTTPException,Depends,File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from huggingface_hub import InferenceClient
import secrets
from typing import Optional
from bson.objectid import ObjectId  # Pour les _id MongoDB
from datetime import datetime, timedelta  # Ajout de timedelta pour expires_at
from fastapi import Request
import requests
import numpy as np
import argparse
import os
from pymongo import MongoClient
from datetime import datetime  # Ajout pour createdAt
from passlib.hash import bcrypt  # Ajout pour le hash du mot de passe
from sentence_transformers import SentenceTransformer
import torch
import PyPDF2
from io import BytesIO
import uuid

SECRET_KEY = secrets.token_hex(32)  # Génère une clé aléatoire

HOST = os.environ.get("API_URL", "0.0.0.0")
PORT = os.environ.get("PORT", 7860)
parser = argparse.ArgumentParser()
parser.add_argument("--host", default=HOST)
parser.add_argument("--port", type=int, default=PORT)
parser.add_argument("--reload", action="store_true", default=True)
parser.add_argument("--ssl_certfile")
parser.add_argument("--ssl_keyfile")
args = parser.parse_args()

# Configuration MongoDB
mongo_uri = os.environ.get("MONGODB_URI", "mongodb+srv://giffardaxel95:TQ5bfvWFqRhkHGVi@chatbotmed.qfn2kdn.mongodb.net/")
db_name = os.environ.get("DB_NAME", "chatmed_schizo")
mongo_client = MongoClient(mongo_uri)
db = mongo_client[db_name]



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




async def get_admin_user(request: Request):
    user = await get_current_user(request)
    if user["role"] != "Administrateur":
        raise HTTPException(status_code=403, detail="Accès interdit: Droits d'administrateur requis")
    return user



# Initialiser le modèle d'embedding (à faire une seule fois au démarrage)
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Erreur lors du chargement du modèle d'embedding: {str(e)}")
    embedder = None
@app.post("/api/admin/knowledge/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = None,
    tags: str = None,
    current_user: dict = Depends(get_admin_user)
):
    try:
        # Vérifier que le fichier est un PDF
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
        
        # Lire le contenu du PDF
        contents = await file.read()
        pdf_file = BytesIO(contents)
        
        # Extraire le texte du PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        for page_num in range(len(pdf_reader.pages)):
            text_content += pdf_reader.pages[page_num].extract_text() + "\n"
        
        # Générer un embedding pour l'ensemble du texte si le modèle est disponible
        embedding = None
        if embedder:
            try:
                # Limiter la taille du texte si nécessaire
                max_length = 5000
                truncated_text = text_content[:max_length]
                embedding = embedder.encode(truncated_text).tolist()
            except Exception as e:
                print(f"Erreur lors de la génération de l'embedding: {str(e)}")
        
        # Générer un identifiant unique pour le document
        doc_id = ObjectId()
        
        # Enregistrer le fichier original 
        pdf_path = f"files/{str(doc_id)}.pdf"
        os.makedirs("files", exist_ok=True)
        with open(pdf_path, "wb") as f:
            pdf_file.seek(0)
            f.write(contents)
        
        # Créer un objet document dans MongoDB
        document = {
            "_id": doc_id,
            "text": text_content,
            "embedding": embedding,
            "title": title or file.filename,
            "tags": tags.split(",") if tags else [],
            "uploaded_by": str(current_user["_id"]),
            "upload_date": datetime.utcnow()
        }
        
        print(f"Tentative d'insertion du document avec ID: {doc_id}")
        result = db.connaissances.insert_one(document)
        print(f"Document inséré avec ID: {result.inserted_id}")
        
        # Vérification de l'insertion
        verification = db.connaissances.find_one({"_id": doc_id})
        if verification:
            print(f"Document vérifié et trouvé dans la base de données")
            return {"success": True, "document_id": str(doc_id)}
        else:
            print(f"ERREUR: Document non trouvé après insertion")
            return {"success": False, "error": "Document non trouvé après insertion"}
        
    except Exception as e:
        import traceback
        print(f"Erreur lors de l'upload du PDF: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/admin/knowledge")
async def list_documents(current_user: dict = Depends(get_admin_user)):
    try:
        # Récupérer les documents triés par date (plus récents en premier)
        documents = list(db.connaissances.find().sort("upload_date", -1))
        
        # Convertir les types non sérialisables (ObjectId, datetime, etc.)
        result = []
        for doc in documents:
            doc_safe = {
                "id": str(doc["_id"]),
                "title": doc.get("title", "Sans titre"),
                "tags": doc.get("tags", []),
                "date": doc.get("upload_date").isoformat() if "upload_date" in doc else None,
                "text_preview": doc.get("text", "")[:100] + "..." if len(doc.get("text", "")) > 100 else doc.get("text", "")
            }
            result.append(doc_safe)
        
        return {"documents": result}
    except Exception as e:
        print(f"Erreur lors de la liste des documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# Fonction pour créer une session
@app.post("/api/login")
async def login(request: Request, response: Response):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        
        # Vérifier les identifiants
        user = db.users.find_one({"email": email})
        if not user or not bcrypt.verify(password, user["password"]):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Créer une session
        session_id = secrets.token_hex(16)
        user_id = str(user["_id"])
        username = f"{user['prenom']} {user['nom']}"
        
        # Stocker la session en base de données
        db.sessions.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        })
        
        # Définir le cookie de session
        response.set_cookie(
            key="session_id", 
            value=session_id, 
            httponly=True,
            max_age=7*24*60*60,  # 7 jours
            samesite="lax"
        )
        
        return {
            "success": True, 
            "username": username, 
            "user_id": user_id,
            "role": user.get("role", "user")  # Ajout du rôle dans la réponse
        }    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    # Vérifier si la session existe et n'est pas expirée
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

@app.delete("/api/admin/knowledge/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_admin_user)):
    try:
        # Convertir l'ID string en ObjectId
        try:
            doc_id = ObjectId(document_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de document invalide")
        
        # Vérifier si le document existe
        document = db.connaissances.find_one({"_id": doc_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Supprimer le document de la base de données
        result = db.connaissances.delete_one({"_id": doc_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Échec de la suppression du document")
        
        # Supprimer le fichier PDF associé s'il existe
        pdf_path = f"files/{document_id}.pdf"
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Fichier supprimé: {pdf_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier: {str(e)}")
                # On continue même si la suppression du fichier échoue
        
        return {"success": True, "message": "Document supprimé avec succès"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")
# Endpoint pour déconnexion
@app.post("/api/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        db.sessions.delete_one({"session_id": session_id})
    
    response.delete_cookie(key="session_id")
    return {"success": True}
@app.post("/api/register")
async def register(request: Request):
    try:
        data = await request.json()
        
        # Validation
        required_fields = ["prenom", "nom", "email", "password"]
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"Le champ {field} est requis")
        
        # Vérifier si l'email existe déjà
        existing_user = db.users.find_one({"email": data["email"]})
        if existing_user:
            raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
        
        # Hash du mot de passe
        hashed_password = bcrypt.hash(data["password"])
        
        # Insérer l'utilisateur (ajouter le rôle par défaut "user")
        user = {
            "prenom": data["prenom"],
            "nom": data["nom"],
            "email": data["email"],
            "password": hashed_password,
            "role": data.get("role", "user"),  # Par défaut "user", peut être "admin"
            "createdAt": datetime.utcnow()
        }
        
        result = db.users.insert_one(user)
        
        return {"message": "Utilisateur créé avec succès", "userId": str(result.inserted_id)}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    
    except HTTPException as he:
        # Re-lever les HTTPException pour FastAPI les traite
        raise he
    
    except Exception as e:
        # Logging détaillé pour débogage
        import traceback
        print(f"Erreur lors de l'inscription: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")





@app.post("/api/embed")
async def embed(request: Request):
    data = await request.json()
    texts = data.get("texts", [])
    
    try:
        # Si vous utilisez un embedder personnalisé
        # embeddings = embedder.encode(texts).tolist()
        
        # Pour déboguer, renvoyez simplement un embedding fictif
        dummy_embedding = [[0.1, 0.2, 0.3] for _ in range(len(texts))]
        
        return {"embeddings": dummy_embedding}
    except Exception as e:
        return {"error": str(e)}

@app.get("/invert")
async def invert(text: str):
    return {
        "original": text,
        "inverted": text[::-1],
    }

HF_TOKEN = os.getenv('REACT_APP_HF_TOKEN')
if not HF_TOKEN:
    raise RuntimeError("Le token Hugging Face (HF_TOKEN) n'est pas défini dans les variables d'environnement.")

# Initialisation du client HF

# Par cette version correcte
hf_client = InferenceClient(token=HF_TOKEN)

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Le champ 'message' est requis.")

    try:
        # Mode développement: simuler une réponse sans appeler l'API
        # Définir des réponses prédéfinies pour simuler l'IA
        dev_responses = [
            "Dans le cadre de la schizophrénie, il est important de noter que ce trouble peut se manifester par des symptômes positifs (hallucinations, délires) et négatifs (retrait social, apathie). Un traitement précoce améliore généralement le pronostic.",
            "Les antipsychotiques sont souvent prescrits comme traitement de première ligne pour la schizophrénie. Ils agissent principalement en bloquant les récepteurs à dopamine D2, mais les mécanismes exacts restent complexes.",
            "La schizophrénie est un trouble multifactoriel impliquant des facteurs génétiques et environnementaux. Les recherches actuelles suggèrent une vulnérabilité neurobiologique qui peut être déclenchée par différents facteurs de stress.",
            "Le soutien psychosocial joue un rôle crucial dans la gestion de la schizophrénie, en complément de la pharmacothérapie. Une approche multimodale est généralement considérée comme la plus efficace.",
            "Les symptômes cognitifs de la schizophrénie peuvent inclure des difficultés de mémoire, d'attention et de fonctions exécutives. Ces aspects sont souvent sous-traités mais affectent significativement la qualité de vie."
        ]
        
        import random
        import time
        
        # Simuler un temps de traitement
        time.sleep(1)
        
        # Choisir une réponse aléatoire
        response = random.choice(dev_responses)
        
        print(f"DEV MODE - Question: {user_message[:50]}... | Réponse simulée")
        
        return {"response": response}
    
    except Exception as e:
        import traceback
        print(f"Erreur détaillée: {traceback.format_exc()}")
        raise HTTPException(status_code=502, detail=f"Erreur: {str(e)}")

@app.get("/data")
async def get_data():
    data = {"data": np.random.rand(100).tolist()}
    return JSONResponse(data)

# Endpoint pour récupérer toutes les conversations d'un utilisateur
@app.get("/api/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        # Récupération des conversations triées par date (les plus récentes d'abord)
        conversations = list(db.conversations.find(
            {"user_id": user_id},
            {"_id": 1, "title": 1, "date": 1, "time": 1, "last_message": 1, "created_at": 1}
        ).sort("created_at", -1))
        
        # Convertir les ObjectId en strings pour la sérialisation JSON
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# Endpoint pour sauvegarder une nouvelle conversation
@app.post("/api/conversations")
async def create_conversation(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
        user_id = str(current_user["_id"])
        
        # Créer la nouvelle conversation
        conversation = {
            "user_id": user_id,
            "title": data.get("title", "Nouvelle conversation"),
            "date": data.get("date"),
            "time": data.get("time"),
            "last_message": data.get("message", ""),
            "created_at": datetime.utcnow()
        }
        
        result = db.conversations.insert_one(conversation)
        
        # Retourner l'ID de la conversation créée
        return {"conversation_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# Endpoint pour sauvegarder un message dans une conversation
@app.post("/api/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
        user_id = str(current_user["_id"])
        
        # Debug pour vérifier les données
        print(f"Ajout message: conversation_id={conversation_id}, sender={data.get('sender')}, text={data.get('text')[:20]}...")
        
        # Vérifier que la conversation appartient à l'utilisateur
        conversation = db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        # Ajouter le message
        message = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "sender": data.get("sender", "user"),
            "text": data.get("text", ""),
            "timestamp": datetime.utcnow()
        }
        
        db.messages.insert_one(message)
        
        # Mettre à jour la dernière activité de la conversation
        db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"last_message": data.get("text", ""), "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True}
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# Endpoint pour récupérer les messages d'une conversation
@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        
        # Vérifier que la conversation appartient à l'utilisateur
        conversation = db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        # Récupérer les messages
        messages = list(db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1))  # Du plus ancien au plus récent
        
        # Convertir les ObjectId en strings pour la sérialisation JSON
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            if "timestamp" in msg:
                msg["timestamp"] = msg["timestamp"].isoformat()
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        
        # Vérifier que la conversation appartient à l'utilisateur
        result = db.conversations.delete_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        # Supprimer également tous les messages associés
        db.messages.delete_many({"conversation_id": conversation_id})
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.get("/")
async def root():
    """Page d'accueil de l'API Medically."""
    return {
        "app_name": "Medically - Assistant IA sur la schizophrénie",
        "version": "1.0.0",
        "api_endpoints": [
            {"path": "/api/login", "method": "POST", "description": "Connexion utilisateur"},
            {"path": "/api/register", "method": "POST", "description": "Création d'un compte"},
            {"path": "/api/chat", "method": "POST", "description": "Poser une question à l'assistant"},
            {"path": "/api/conversations", "method": "GET", "description": "Liste des conversations"},
            {"path": "/api/conversations/{id}/messages", "method": "GET", "description": "Messages d'une conversation"}
        ],
        "documentation": "/docs",
        "status": "En ligne",
        "environment": "Développement"
    }
if __name__ == "__main__":
    import uvicorn

    print(args)
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile,
    )

