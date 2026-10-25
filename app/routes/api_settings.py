from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.database import get_all_settings, update_settings, get_scheduler_logs
from app.scheduler import run_autopilot_cycle, update_scheduler_interval

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

@router.get("")
def get_settings():
    return {"success": True, "settings": get_all_settings()}

@router.post("")
def save_settings(req: SettingsUpdateRequest):
    update_settings(req.settings)
    
    # Update scheduler interval if changed
    if "autopilot_interval_hours" in req.settings:
        try:
            update_scheduler_interval(req.settings["autopilot_interval_hours"])
        except Exception as e:
            print(f"Error rescheduling: {e}")
            
    return {"success": True, "message": "Settings updated successfully!", "settings": get_all_settings()}

@router.post("/autopilot/trigger")
def trigger_autopilot():
    result = run_autopilot_cycle(manual_trigger=True)
    return result

@router.get("/autopilot/logs")
def get_logs(limit: int = 30):
    logs = get_scheduler_logs(limit=limit)
    return {"success": True, "logs": logs}

@router.post("/sync-vault")
def sync_vault(req: SettingsUpdateRequest):
    """
    Called by client on startup with localStorage vault data.
    Ensures that if Render container rebooted or database reset,
    user credentials (FB Page ID, Token, TG Token) are instantly restored to SQLite.
    """
    current = get_all_settings()
    updates = {}
    for k, v in req.settings.items():
        if v and str(v).strip():
            # If current setting is empty or default, update it with client's saved vault
            if not current.get(k) or current.get(k) == "":
                updates[k] = v
            # Always ensure tokens and IDs are synced if client has them
            elif k in ["fb_page_id", "fb_access_token", "telegram_bot_token", "telegram_channel_id"]:
                updates[k] = v

    if updates:
        update_settings(updates)
        return {"success": True, "synced_count": len(updates), "settings": get_all_settings()}
    return {"success": True, "synced_count": 0, "settings": current}

@router.get("/backup")
def backup_settings():
    """Returns all settings for client download/export."""
    return {"success": True, "vault": get_all_settings()}

@router.post("/restore")
def restore_settings(req: SettingsUpdateRequest):
    """Restores settings from an uploaded JSON backup."""
    update_settings(req.settings)
    return {"success": True, "message": "Settings restored successfully!", "settings": get_all_settings()}
