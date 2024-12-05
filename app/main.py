from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.api.routes import query
from app.api.routes import tools
from app.api.routes import chat
from app.api.routes import health

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(title=settings.API_TITLE)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Include routers without the /api prefix since Choreo adds it
app.include_router(query.router)
app.include_router(tools.router)
app.include_router(chat.router)
app.include_router(health.router)  