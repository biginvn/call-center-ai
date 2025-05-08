import os
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
import asyncio

@pytest.mark.asyncio
async def test_mongodb_connection():
    mongodb_url = os.getenv("MONGODB_URL")

    assert mongodb_url is not None, "MONGODB_URL env variable not set"

    try:
        client = AsyncIOMotorClient(mongodb_url)
        result = await client.admin.command('ping')
        assert result["ok"] == 1.0
    except Exception as e:
        pytest.fail(f"Lỗi kết nối: {str(e)}")
    finally:
        # Đóng kết nối
        client.close()

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())