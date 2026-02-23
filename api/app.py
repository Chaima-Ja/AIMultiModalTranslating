"""FastAPI application for translation pipeline."""
import os
import uuid
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from models import JobRecord
from pipeline import TranslationPipeline


app = FastAPI(title="Translation Pipeline API", version="1.0.0")

# CORS middleware for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
config = Config.from_env()

# In-memory job store
jobs: Dict[str, JobRecord] = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc",
    ".pptx", ".ppt",
    ".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac"
}


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


async def run_translation(job_id: str, input_path: str):
    """Background task to run translation pipeline."""
    job = jobs[job_id]
    job.status = "running"
    start_time = time.time()
    
    try:
        pipeline = TranslationPipeline(config)
        
        def progress_callback(done: int, total: int, block_id: str):
            job.blocks_done = done
            job.blocks_total = total
            job.progress = int((done / total) * 100) if total > 0 else 0
        
        output_path = await pipeline.translate_file(
            input_path,
            progress_callback=progress_callback
        )
        
        job.output_path = output_path
        job.status = "done"
        job.progress = 100
        job.blocks_done = job.blocks_total
        
        await pipeline.close()
    
    except Exception as e:
        job.status = "failed"
        error_msg = str(e)
        
        # Provide user-friendly error messages
        if ".doc" in error_msg.lower() or "not a word file" in error_msg.lower() or "not a valid word" in error_msg.lower():
            error_msg = (
                "The .doc format (old binary Word format) is not supported. "
                "This system only supports .docx (Office Open XML) format.\n\n"
                "To fix this:\n"
                "1. Open the file in Microsoft Word and save as .docx\n"
                "2. Or use LibreOffice: soffice --convert-to docx yourfile.doc\n"
                "3. Or use an online converter\n\n"
                f"Original error: {error_msg}"
            )
        elif "not a valid" in error_msg.lower() and "document" in error_msg.lower():
            error_msg = (
                "The uploaded file is not a valid document format.\n\n"
                f"Details: {error_msg}"
            )
        
        job.error = error_msg
        print(f"Translation failed for job {job_id}: {error_msg}")
    
    finally:
        job.duration_seconds = time.time() - start_time
        # Clean up input file after processing
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass


@app.post("/translate")
async def translate_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a file for translation.
    
    Returns immediately with a job_id. Use GET /status/{job_id} to check progress.
    """
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Save uploaded file
    os.makedirs(config.upload_dir, exist_ok=True)
    ext = Path(file.filename).suffix
    input_path = os.path.join(config.upload_dir, f"{job_id}{ext}")
    
    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create job record
    job = JobRecord(
        job_id=job_id,
        status="pending",
        filename=file.filename,
        progress=0,
        blocks_total=0,
        blocks_done=0
    )
    jobs[job_id] = job
    
    # Start background translation task
    background_tasks.add_task(run_translation, job_id, input_path)
    
    return {
        "job_id": job_id,
        "message": "Translation job started",
        "status_url": f"/status/{job_id}"
    }


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get the status of a translation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "blocks_done": job.blocks_done,
        "blocks_total": job.blocks_total,
        "error": job.error,
        "duration_seconds": job.duration_seconds
    }


@app.get("/download/{job_id}")
async def download_file(job_id: str):
    """Download the translated file."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not complete. Current status: {job.status}"
        )
    
    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    # Determine content type
    ext = Path(job.output_path).suffix.lower()
    media_type_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".srt": "text/plain",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac"
    }
    media_type = media_type_map.get(ext, "application/octet-stream")
    
    return FileResponse(
        job.output_path,
        media_type=media_type,
        filename=Path(job.output_path).name
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "backend": config.translator_backend,
        "ollama_url": config.ollama_url,
        "ollama_model": config.ollama_model
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

