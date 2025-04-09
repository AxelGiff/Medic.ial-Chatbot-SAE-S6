from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router  
app = FastAPI()

app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)