import httpx
import shutil
import os
import zipfile
from fastapi import HTTPException

# In a real app, this should be configurable
STORAGE_DIR = "storage/repos"

async def fetch_repo_zip(repo_url: str, job_id: str):
    """
    Downloads the repository ZIP from GitHub and extracts it.
    Assumes repo_url is https://github.com/owner/repo or similar.
    """
    if "github.com" not in repo_url:
        raise HTTPException(status_code=400, detail="Only GitHub repos are supported")

    # Construct the ZIP URL (assuming 'main' or 'master' branch usually, but GitHub redirects usually work for /archive/HEAD.zip)
    # GitHub URL: https://github.com/owner/repo
    # Archive URL: https://github.com/owner/repo/archive/refs/heads/main.zip OR shorter: https://github.com/owner/repo/archive/HEAD.zip
    
    zip_url = f"{repo_url}/archive/HEAD.zip"
    target_dir = os.path.join(STORAGE_DIR, str(job_id))
    os.makedirs(target_dir, exist_ok=True)
    
    zip_path = os.path.join(target_dir, "repo.zip")
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(zip_url)
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(resp.content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download repo: {str(e)}")

    # Extract ZIP
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # We want to extract to target_dir. 
            # GitHub zips usually have a top-level folder like 'repo-main'.
            zip_ref.extractall(target_dir)
            
        # Cleanup ZIP file
        os.remove(zip_path)
        
        # Find the root extracted folder
        extracted_folders = [f for f in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, f))]
        if len(extracted_folders) == 1:
            repo_root = os.path.join(target_dir, extracted_folders[0])
            return repo_root
        else:
            return target_dir # Fallback if structure is weird (e.g. flat)
            
    except zipfile.BadZipFile:
        raise HTTPException(status_code=500, detail="Invalid ZIP file downloaded")
