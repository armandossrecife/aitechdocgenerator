from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from .auth import get_current_user

router = APIRouter(prefix="/repos", tags=["repos"])

@router.post("/", response_model=schemas.RepositoryResponse)
def create_repository(repo: schemas.RepositoryCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Basic validation (assume it's a valid github url for MVP)
    # Extract name from URL (simple logic)
    # expected format: https://github.com/owner/repo or just owner/repo
    url = repo.url.strip()
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
    else:
        parts = url.split("/")
    
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL or identifiers")
    
    full_name = f"{parts[0]}/{parts[1]}".replace(".git", "")
    
    new_repo = models.Repository(
        user_id=current_user.id,
        full_name=full_name,
        url=f"https://github.com/{full_name}"
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)
    return new_repo

@router.get("/", response_model=List[schemas.RepositoryResponse])
def read_repositories(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    repos = db.query(models.Repository).filter(models.Repository.user_id == current_user.id).offset(skip).limit(limit).all()
    return repos

@router.delete("/{id}")
def delete_repository(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    repo = db.query(models.Repository).filter(models.Repository.id == id, models.Repository.user_id == current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    db.delete(repo)
    db.commit()
    return {"ok": True}
