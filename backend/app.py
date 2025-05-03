import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import argparse

from database import init_mongodb
import auth, chat, conversations, admin

app = FastAPI(title="Medic.ial", description="Assistant IA spécialisé sur la maladie de la schizophrénie")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_mongodb()

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(admin.router)



app.mount("/", StaticFiles(directory="static", html=True), name="static")
'''
@app.get("/")
async def root():
    """Page d'accueil de l'API Medic.ial."""
    return {
        "app_name": "Medic.ial - Assistant IA sur la schizophrénie",
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
    '''
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=config.HOST) 
    parser.add_argument("--port", type=int, default=config.PORT)  
    parser.add_argument("--reload", action="store_true", default=True)
    parser.add_argument("--ssl_certfile")
    parser.add_argument("--ssl_keyfile")
    args = parser.parse_args()

    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile,
    )