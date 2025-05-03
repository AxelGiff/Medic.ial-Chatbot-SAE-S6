import os
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import MONGODB_URI, DB_NAME, SAVE_FOLDER

PDF_URLS = [
    
]

COLLECTION_NAME = "connaissances"

def download_pdf(url, save_path, retries=2, delay=3):
    """Télécharge un PDF depuis une URL avec gestion des erreurs."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req) as response, open(save_path, 'wb') as f:
                f.write(response.read())
            print(f"Téléchargé : {save_path}")
            return
        except (HTTPError, URLError) as e:
            print(f"Erreur ({e}) pour {url}, tentative {attempt+1}/{retries}")
            time.sleep(delay)
    print(f"Échec du téléchargement : {url}")
'''
def init_documents():
    """Initialise les documents dans la base de données avec leurs embeddings."""
    os.makedirs(SAVE_FOLDER, exist_ok=True)

   
    for url in PDF_URLS:
        file_name = url.split("/")[-1]
        file_path = os.path.join(SAVE_FOLDER, file_name)
        if not os.path.exists(file_path):
            download_pdf(url, file_path)

    print("Chargement des PDFs...")
    loader = PyPDFDirectoryLoader(SAVE_FOLDER)
    docs = loader.load()

    print("Découpage des documents...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    print(f"{len(chunks)} morceaux extraits.")

    print("Initialisation du modèle d'embeddings...")
    embedding_model = HuggingFaceEmbeddings(model_name="shtilev/medical_embedded_v2")

    print("Connexion à MongoDB...")
    client = MongoClient(MONGODB_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    confirm = input("Cette opération supprimera toutes les données existantes. Continuer? (o/n): ")
    if confirm.lower() != 'o':
        print("Opération annulée.")
        return

    print("Suppression des documents existants...")
    collection.delete_many({})

    print("Génération des embeddings et insertion dans la base de données...")
    for i, chunk in enumerate(chunks):
        text = chunk.page_content
        print(f"Traitement du morceau {i+1}/{len(chunks)}")
        embedding = embedding_model.embed_query(text)
        collection.insert_one({
            "text": text,
            "embedding": embedding
        })

    print("Tous les embeddings ont été insérés dans la base MongoDB.")

if __name__ == "__main__":
    init_documents()
    '''