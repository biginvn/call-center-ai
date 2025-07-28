from fastapi import APIRouter
from app.models.extension import Extension
from app.models.user import User

router = APIRouter(prefix="/extensions", tags=["extensions"])

@router.get("/available")
async def get_available_extensions():
    # Lấy tất cả user có extension_number không rỗng
    users_with_extensions = await User.find({"extension_number": {"$ne": ""}}).to_list()

    # Trích ra danh sách extension_number đang được dùng
    used_numbers = {user.extension_number for user in users_with_extensions}

    # Trả về các extension chưa bị dùng
    available_extensions = await Extension.find({
        "extension_number": {"$nin": list(used_numbers)}
    }).to_list()

    return available_extensions
