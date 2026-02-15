from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
import os
from .. import models, schemas, database
from .auth import get_current_user
from ..services import github_fetcher, context_builder, ollama_client, doc_generator

router = APIRouter(prefix="/analyses", tags=["analyses"])

async def run_analysis_pipeline(job_id: int, repo_url: str, db: Session):
    # This function runs in the background
    # 1. Update status to RUNNING
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
    if not job:
        return
    job.status = models.JobStatus.RUNNING
    db.commit()

    try:
        # 2. Fetch Repo
        repo_path = await github_fetcher.fetch_repo_zip(repo_url, str(job_id))
        
        # 3. Build Evidence
        evidence = context_builder.build_context(repo_path)
        
        # Save evidence to DB (optional, good for debugging)
        job.evidence_json = json.dumps(evidence)
        db.commit()
        
        # 4. Call LLM (Sprint 3)
        # Note: We haven't implemented ollama_client/doc_generator yet, so we'll mock or leave TODO
        markdown_doc = await doc_generator.generate_documentation(evidence)
        
        # 5. Save Document
        doc = models.Document(
            job_id=job.id,
            content_md=markdown_doc
        )
        db.add(doc)
        
        # 6. Mark DONE
        job.status = models.JobStatus.DONE
        job.finished_at = models.datetime.utcnow()
        db.commit()
        
    except Exception as e:
        job.status = models.JobStatus.ERROR
        job.error_message = str(e)
        db.commit()
        print(f"Job {job_id} failed: {e}")

@router.post("/", response_model=schemas.JobResponse)
def start_analysis(
    repository_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    repo = db.query(models.Repository).filter(models.Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    # Create Job
    job = models.AnalysisJob(repository_id=repo.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger Background Task
    background_tasks.add_task(run_analysis_pipeline, job.id, repo.url, db)
    
    return job

@router.get("/{id}", response_model=schemas.JobResponse)
def get_analysis_status(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{id}/document")
def get_analysis_document(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Check job ownership via repo (simplified)
    # properly we should check repo owner
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job or not job.documents:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {"markdown": job.documents[0].content_md}

@router.get("/{id}/download_pdf")
def download_pdf(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job or not job.documents:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc = job.documents[0]
    md_content = doc.content_md
    
    # Define PDF path
    pdf_filename = f"report_{id}.pdf"
    pdf_path = os.path.join("storage/docs", pdf_filename)
    os.makedirs("storage/docs", exist_ok=True)
    
    # Convert if not exists (or always overwrite for simplicity)
    from ..services.pdf_generator import convert_md_to_pdf
    convert_md_to_pdf(md_content, pdf_path)
    
    from fastapi.responses import FileResponse
    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_filename)
