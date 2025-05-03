from pymongo import MongoClient
import os
from config import MONGODB_URI, DB_NAME, SAVE_FOLDER

mongo_client = None
db = None

def init_mongodb():
    """Initialise la connexion à MongoDB."""
    global mongo_client, db
    
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[DB_NAME]
    
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    
    doc_count = db.connaissances.count_documents({})
    print(f"\n[DIAGNOSTIC] Collection 'connaissances': {doc_count} documents trouvés")
    
    if doc_count == 0:
        print("[AVERTISSEMENT] La collection est vide. Le système RAG ne fonctionnera pas!")
    else:
        sample_doc = db.connaissances.find_one({})
        has_embeddings = "embedding" in sample_doc and sample_doc["embedding"] is not None
        print(f"[DIAGNOSTIC] Les documents ont des embeddings: {'✅ Oui' if has_embeddings else '❌ Non'}")
    
    return db

def get_db():
    """Récupère l'instance de la base de données."""
    global db
    if db is None:
        return init_mongodb()
    return db