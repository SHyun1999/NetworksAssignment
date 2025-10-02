from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os, re, time

app = FastAPI(title="Image Upload Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")

def sanitize_filename(name: str) -> str:
    base = os.path.basename(name)
    base = SAFE_NAME.sub("_", base)
    return base or f"file_{int(time.time())}"

@app.get("/", tags=["health"])
def root():
    return {"ok": True, "message": "FastAPI alive"}

@app.get("/uploads", response_model=List[str], tags=["files"])
def list_uploads():
    files = sorted([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))])
    return files

@app.get("/uploads/{filename}", tags=["files"])
def get_file(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(filepath)

@app.post("/upload", tags=["upload"])
async def upload_image(file: UploadFile = File(...)):
    if not (file.content_type and file.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="only image files are allowed")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    original = sanitize_filename(file.filename or "image")
    saved_name = f"{timestamp}_{original}"
    save_path = os.path.join(UPLOAD_DIR, saved_name)

    try:
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"save failed: {e}")

    return JSONResponse(
        {
            "filename": saved_name,
            "message": "upload ok",
            "path": f"uploads/{saved_name}",
            "size_bytes": len(contents),
            "content_type": file.content_type,
        }
    )
