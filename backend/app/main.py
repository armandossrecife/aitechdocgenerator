from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, repos, analyses

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Github Repo Analyzer")

app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(analyses.router)

@app.get("/")
def read_root():
    return {"message": "API is running"}
