from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os

app = Flask(__name__)
app.secret_key = "flask_secret_key"  # Change for production
API_URL = "http://127.0.0.1:8000"

@app.route("/")
def index():
    if "access_token" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            response = requests.post(f"{API_URL}/auth/token", data={"username": email, "password": password})
            
            if response.status_code == 200:
                token_data = response.json()
                session["access_token"] = token_data["access_token"]
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials")
        except requests.exceptions.ConnectionError:
            flash("Could not connect to backend server. Is it running?")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        payload = {"name": name, "email": email, "password": password}
        try:
            response = requests.post(f"{API_URL}/auth/register", json=payload)
            
            if response.status_code == 200:
                flash("Registration successful! Please login.")
                return redirect(url_for("login"))
            else:
                flash(f"Error: {response.text}")
        except requests.exceptions.ConnectionError:
             flash("Could not connect to backend server.")
            
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "access_token" not in session:
        return redirect(url_for("login"))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    try:
        # Get User Info
        user_resp = requests.get(f"{API_URL}/auth/me", headers=headers)
        if user_resp.status_code == 401:
             session.clear()
             return redirect(url_for("login"))
             
        user = user_resp.json()
        
        # Get Repos
        repos_resp = requests.get(f"{API_URL}/repos/", headers=headers)
        repos = repos_resp.json() if repos_resp.status_code == 200 else []
        
        # Enrich repos with analysis status (Optional, skipping for MVP complexity)
        # But we need basic flow.
        
        return render_template("dashboard.html", user=user, repos=repos)
    except requests.exceptions.ConnectionError:
        flash("Backend unreachable")
        return render_template("dashboard.html", user={"name": "Offline User"}, repos=[])


@app.route("/repos/add", methods=["POST"])
def add_repo():
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    url = request.form.get("url")
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    requests.post(f"{API_URL}/repos/", json={"url": url}, headers=headers)
    return redirect(url_for("dashboard"))

@app.route("/repos/delete/<int:repo_id>")
def delete_repo(repo_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    requests.delete(f"{API_URL}/repos/{repo_id}", headers=headers)
    return redirect(url_for("dashboard"))

@app.route("/analyses/start/<int:repo_id>", methods=["POST"])
def start_analysis_route(repo_id):
    if "access_token" not in session:
         return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    # For query params in POST (FastAPI expects ?repository_id=X)
    resp = requests.post(f"{API_URL}/analyses/?repository_id={repo_id}", headers=headers, json={})
    
    if resp.status_code == 200:
        job = resp.json()
        return redirect(url_for("view_analysis", job_id=job["id"]))
    else:
        flash(f"Failed to start analysis: {resp.text}")
        return redirect(url_for("dashboard"))

@app.route("/analyses/<int:job_id>")
def view_analysis(job_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    resp = requests.get(f"{API_URL}/analyses/{job_id}", headers=headers)
    
    if resp.status_code != 200:
        flash("Analysis Job not found")
        return redirect(url_for("dashboard"))
        
    job = resp.json()
    document = ""
    
    if job["status"] == "DONE":
        doc_resp = requests.get(f"{API_URL}/analyses/{job_id}/document", headers=headers)
        if doc_resp.status_code == 200:
             document = doc_resp.json().get("markdown", "")
    
    return render_template("analysis_result.html", job=job, document=document)

@app.route("/analyzed-repos")
def analyzed_repos():
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    try:
        # Fetch all repos
        repos_resp = requests.get(f"{API_URL}/repos/", headers=headers)
        if repos_resp.status_code != 200:
            flash("Error fetching repositories")
            return redirect(url_for("dashboard"))
            
        all_repos = repos_resp.json()
        
        # Filter for repos with at least one DONE job
        analyzed_list = []
        for repo in all_repos:
            # Sort jobs by id desc to get latest?
            # Schema includes 'jobs' list now
            valid_jobs = [j for j in repo.get("jobs", []) if j["status"] == "DONE"]
            if valid_jobs:
                # Get the latest one
                # Assuming jobs are returned, we pick the last one or sort
                # Safety sort
                valid_jobs.sort(key=lambda x: x["id"], reverse=True)
                last_job = valid_jobs[0]
                
                analyzed_list.append({
                    "repo": repo,
                    "last_job": last_job
                })
        
        return render_template("analyzed_repos.html", analyzed_repos=analyzed_list)
        
    except Exception as e:
        print(e)
        flash(f"Error: {e}")
        return redirect(url_for("dashboard"))

@app.route("/analyses/<int:job_id>/pdf")
def download_pdf_route(job_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    # Proxy the request to backend
    # We use stream=True to handle potential large files? For PDF it's fine to just load it.
    # But usually we want to return the response object from flask
    
    backend_url = f"{API_URL}/analyses/{job_id}/download_pdf"
    
    try:
        req = requests.get(backend_url, headers=headers, stream=True)
        
        if req.status_code == 200:
             # Stream back to client
             from flask import Response, stream_with_context
             return Response(stream_with_context(req.iter_content(chunk_size=1024)), 
                             content_type=req.headers['Content-Type'],
                             headers={"Content-Disposition": f"attachment; filename=report_{job_id}.pdf"})
        else:
             flash("Could not generate/download PDF")
             return redirect(url_for("view_analysis", job_id=job_id))
    except Exception as e:
        flash(f"Error downloading PDF: {e}")
        return redirect(url_for("view_analysis", job_id=job_id))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(port=5001, debug=True)
