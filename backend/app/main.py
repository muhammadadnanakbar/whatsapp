from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.services import copy_group_members, find_groups_by_name, group_display_name, group_id
from backend.app.waha_client import WahaClient, WahaError

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "static"

app = FastAPI(title="WhatsApp Group Copier", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class CopyGroupRequest(BaseModel):
    source_group_name: str = Field(..., min_length=1, description="Name of existing group to copy from")
    new_group_name: str = Field(..., min_length=1, description="Name for the new group")
    source_group_id: str | None = Field(None, description="Use when multiple groups match the name")


class GroupSearchQuery(BaseModel):
    q: str = ""


def get_client() -> WahaClient:
    return WahaClient(get_settings())


@app.get("/")
async def index():
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {"message": "Static UI not found. Place index.html in static/"}


@app.get("/api/health")
async def health():
    settings = get_settings()
    client = get_client()
    try:
        me = await client.get_session_me()
        return {
            "ok": True,
            "waha_base_url": settings.waha_base_url,
            "session": settings.waha_session,
            "me": me,
        }
    except WahaError as exc:
        raise HTTPException(
            status_code=502,
            detail={"message": str(exc), "waha": exc.detail},
        ) from exc


@app.get("/api/groups")
async def list_groups(q: str = ""):
    client = get_client()
    try:
        groups = await client.list_groups()
        items = [
            {
                "id": group_id(g),
                "name": group_display_name(g),
                "size": g.get("size") or g.get("participantsCount"),
            }
            for g in groups
        ]
        if q.strip():
            matched = find_groups_by_name(groups, q)
            items = [
                {
                    "id": group_id(g),
                    "name": group_display_name(g),
                    "size": g.get("size") or g.get("participantsCount"),
                }
                for g in matched
            ]
        return {"groups": items, "count": len(items)}
    except WahaError as exc:
        raise HTTPException(status_code=502, detail={"message": str(exc), "waha": exc.detail}) from exc


@app.post("/api/groups/copy")
async def copy_group(body: CopyGroupRequest):
    client = get_client()
    settings = get_settings()
    try:
        result = await copy_group_members(
            client,
            settings,
            source_group_name=body.source_group_name.strip(),
            new_group_name=body.new_group_name.strip(),
            source_group_id=body.source_group_id,
        )
        if result.get("status") == "ambiguous":
            return result
        return result
    except WahaError as exc:
        raise HTTPException(
            status_code=502,
            detail={"message": str(exc), "waha": exc.detail},
        ) from exc
