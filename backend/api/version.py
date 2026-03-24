from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/version")
async def get_version():
    """获取应用版本"""
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "version.py")
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            version = f.read().strip()
        return {"code": 200, "data": {"version": version}}
    except Exception as e:
        return {"code": 200, "data": {"version": "1.0.0"}}
