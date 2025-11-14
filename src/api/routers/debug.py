"""Debug endpoints for troubleshooting (development only)."""
from fastapi import APIRouter
from src.memory.memory_manager import MemoryManager

router = APIRouter()
_memory_manager = MemoryManager()


@router.get("/profile/{user_id}")
async def debug_get_profile(user_id: str):
    """Debug endpoint to see what profile data exists for a user."""
    try:
        profile = _memory_manager.load_profile(user_id)
        return {
            "user_id": user_id,
            "profile_found": profile is not None,
            "profile_data": profile or {},
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "error": str(e),
            "profile_found": False,
        }
