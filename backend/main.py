
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import analysis, upload, metrics

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(analysis.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://bia-project-frontend.vercel.app", # Placeholder for your Vercel deployment
        "*" # Allow all for initial testing/LinkedIn demo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.models.schema import Base
from sqlalchemy import create_engine

@app.on_event("startup")
def startup_event():
    # Naive DB init for prototype
    # In production use Alembic migrations
    try:
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("Database tables created.")

    except Exception as e:
        print(f"Warning: DB connection failed ({e}). Running without persistence.")

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.ENV}

@app.get("/")
def read_root():
    return {"message": "Welcome to BIA Analyst API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
