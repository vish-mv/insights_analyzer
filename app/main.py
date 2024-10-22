from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.api.routes import query
from app.api.routes import tools
from app.api.routes import chat

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

# Include routers
app.include_router(query.router, prefix=settings.API_PREFIX)
app.include_router(tools.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)


# Root endpoint serving the query interface
@app.get("/", response_class=HTMLResponse)
async def get_query_interface(request: Request):  # Add request parameter
    return templates.TemplateResponse(
        "index.html",
        {"request": request}  # Pass the request object
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG_MODE
    )