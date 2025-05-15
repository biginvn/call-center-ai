import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from app.core.config import settings
from app.core.database import init_db, close_db, get_database
from app.models.user import User

async def reset_database():
    db = get_database()
    await db.drop_collection("User")
    print("Database đã được reset.")

async def seed_data():
    """Thêm dữ liệu seed vào database."""
    # Kiểm tra xem đã có user nào chưa
    user_count = await User.count()
    if user_count > 0:
        print("Database đã có dữ liệu. Bỏ qua seeding.")
        return

    # Danh sách user để seed
    users = [
        User(username="admin", fullname="Admin",email="admin@gmail.com", password="123456", extension_number="", role="admin", status=""),
        User(username="khoa", fullname="Lê Anh Khoa",email="khoa@gmail.com", password="123456", extension_number="", role="agent", status=""),
        User(username="thanh", fullname="Nguyễn Phúc Thành",email="thanh@gmail.com", password="123456", extension_number="", role="agent", status=""),
        User(username="manh", fullname="Trần Văn Mạnh",email="manh@gmail.com", password="123456", extension_number="", role="agent", status=""),
    ]

    # Thêm user vào database
    for user in users:
        await user.insert()
        print(f"Đã thêm user: {user.username} với role: {user.role}")

async def main():
    await init_db()
    await reset_database()  # Reset database trước khi seed
    await seed_data()
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())