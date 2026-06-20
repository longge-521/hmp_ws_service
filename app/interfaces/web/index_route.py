import os
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Web"])

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

@router.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>WebSocket Client Index HTML is missing.</h3>"

@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

