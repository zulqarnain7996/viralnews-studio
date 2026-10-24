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
