import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.ai_agent import format_announcement
from backend.whatsapp_bot import bot_instance, send_to_multiple_groups

app = FastAPI(title="WhatsApp AI Announcement Bot", version="1.1.0")

# Restrict CORS to localhost and local network origins rather than wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8050",
        "http://127.0.0.1:8050",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
history_lock = asyncio.Lock()

def load_history() -> list:
    """Reads saved announcement history from history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

async def save_history_entry(entry: dict):
    """Appends an announcement execution record to history.json with thread/async lock."""
    async with history_lock:
        history = load_history()
        history.insert(0, entry)  # newest first
        history = history[:50]
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Warning] Failed to write history: {e}")

class GenerateRequest(BaseModel):
    raw_text: str = Field(..., max_length=15000)
    template: Optional[str] = "General"

class AnnouncementRequest(BaseModel):
    raw_text: Optional[str] = Field("", max_length=15000)
    group_names: List[str]
    formatted_message: Optional[str] = Field(None, max_length=20000)
    template: Optional[str] = "General"

@app.get("/")
def root():
    """Serves the frontend dashboard directly when opening localhost:8000."""
    frontend_path = PROJECT_ROOT / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"status": "ok", "message": "WhatsApp AI Announcement API is running."}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "WhatsApp AI Announcement Bot"}

# --- STEP 1 & 2: WHATSAPP SESSION & GROUP DISCOVERY ---

@app.post("/api/whatsapp/open")
async def open_whatsapp_session():
    """
    Step 1: Opens the WhatsApp Web browser window.
    The user can scan the QR code (if needed) or resume an existing session.
    """
    try:
        res = await bot_instance.open_whatsapp()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/whatsapp/status")
async def get_whatsapp_status():
    """Returns current WhatsApp connection state ('logged_in', 'waiting_qr', 'disconnected')."""
    return await bot_instance.get_status()

@app.get("/api/whatsapp/groups")
async def get_whatsapp_groups():
    """
    Step 2: Scrapes and returns active group/chat names from WhatsApp Web.
    """
    try:
        groups = await bot_instance.fetch_groups()
        return {"groups": groups, "count": len(groups)}
    except TimeoutError as te:
        raise HTTPException(status_code=400, detail=str(te))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/whatsapp/close")
async def close_whatsapp_session():
    """Closes the browser session."""
    try:
        await bot_instance.close()
        return {"status": "closed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- STEP 3: UPLOAD & FORMAT ANNOUNCEMENT ---

class UploadRequest(BaseModel):
    filename: Optional[str] = "notes.txt"
    content: str

@app.post("/api/upload-announcement")
async def upload_announcement_file(data: UploadRequest):
    """
    Step 3: Accepts text content from an uploaded file (.txt, .md, .csv, .json, .log).
    """
    return {"filename": data.filename, "text": data.content}

@app.post("/api/generate-announcement")
async def generate_preview(data: GenerateRequest):
    """
    Transforms raw notes or uploaded draft into a styled WhatsApp announcement.
    Runs non-blocking on threadpool to avoid stalling the event loop.
    """
    try:
        if not data.raw_text.strip():
            raise HTTPException(status_code=400, detail="Raw text cannot be empty.")
        
        loop = asyncio.get_running_loop()
        formatted = await loop.run_in_executor(
            None,
            format_announcement,
            data.raw_text,
            data.template or "General"
        )
        return {"formatted_message": formatted}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while generating announcement.")

# --- STEP 4: BROADCAST DISPATCH ---

@app.post("/api/broadcast")
async def broadcast_announcement(request: AnnouncementRequest):
    """
    Step 4: Broadcasts the announcement to the selected WhatsApp groups.
    """
    try:
        if not request.group_names:
            raise HTTPException(status_code=400, detail="Please select or enter at least one target group.")
        
        # 1. Determine formatted message
        if request.formatted_message and request.formatted_message.strip():
            formatted_message = request.formatted_message.strip()
        else:
            if not (request.raw_text and request.raw_text.strip()):
                raise HTTPException(status_code=400, detail="Please provide instructions or an announcement.")
            loop = asyncio.get_running_loop()
            formatted_message = await loop.run_in_executor(
                None,
                format_announcement,
                request.raw_text,
                request.template or "General"
            )
        
        # 2. Dispatch via active WhatsApp Bot instance
        status = await bot_instance.broadcast_announcement(request.group_names, formatted_message)
        
        # 3. Save entry to history
        record = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "template": request.template or "General",
            "group_names": request.group_names,
            "raw_text": request.raw_text or "",
            "formatted_message": formatted_message,
            "delivery_status": status
        }
        await save_history_entry(record)

        return {
            "success": True,
            "formatted_message": formatted_message,
            "delivery_status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broadcast error: {str(e)}")

@app.get("/api/history")
def get_history():
    """Returns past broadcast records."""
    return load_history()

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print(" 🚀 WhatsApp AI Bot is starting...")
    print(" 🌐 Dashboard URL: http://127.0.0.1:8050")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8050)
