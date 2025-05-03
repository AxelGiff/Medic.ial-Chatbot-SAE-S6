import os
import secrets

# Serveur
HOST = os.getenv("API_URL", "0.0.0.0")
PORT = int(os.getenv("PORT", "7860"))

# Sécurité
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Base de données
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://giffardaxel95:TQ5bfvWFqRhkHGVi@chatbotmed.qfn2kdn.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "chatmed_schizo")

# HuggingFace
HF_TOKEN = os.getenv('REACT_APP_HF_TOKEN')

# Dossiers
SAVE_FOLDER = "files"

# CORS
CORS_ORIGINS = [
    "https://axl95-medically.hf.space",
    "https://huggingface.co",
    "http://localhost:3000",
    "http://localhost:7860",
    "http://0.0.0.0:7860"
]

# Modèles
EMBEDDING_MODEL = "shtilev/medical_embedded_v2"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# Limites
MAX_TOKENS = 2000