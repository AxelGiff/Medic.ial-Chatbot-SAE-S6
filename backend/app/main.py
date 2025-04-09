from fastapi import FastAPI
from app.routes import router  # Garde app.routes si routes.py est dans le dossier app/

app = FastAPI()

app.include_router(router)
