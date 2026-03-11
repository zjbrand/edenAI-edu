# backend/app/api/admin.py
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
def admin_overview():
    """管理APIの疎通確認用（/admin/system/status は admin_system.py を利用）"""
    return {"ok": True, "message": "admin router is active"}
