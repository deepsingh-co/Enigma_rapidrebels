from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import routes
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WasteX API")

# Read comma-separated origins from .env, fallback to standard local dev ports
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
origins = [url.strip() for url in frontend_url.split(",") if url.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to WasteX API"}
