from app.models.active import ActiveUser
from app.models.user import User
from fastapi import HTTPException
from app.auth.exceptions import CustomHTTPException

async def add_active_user(user: User):
    active_user_doc = await ActiveUser.find_one()
    if not active_user_doc:
        active_user_doc = ActiveUser(active_user=[user])
        await active_user_doc.insert()
    else:
        if not any(u.id == user.id for u in active_user_doc.active_user):
            active_user_doc.active_user.append(user)
            await active_user_doc.save()
    return active_user_doc

async def remove_active_user(user: User):
    active_user_doc = await ActiveUser.find_one()
    if not active_user_doc:
        raise HTTPException(status_code=404, detail="No active user list found")

    active_user_doc.active_user = [u for u in active_user_doc.active_user if u.id != user.id]
    await active_user_doc.save()
    return active_user_doc

async def get_active_users():
    active_user_doc = await ActiveUser.find_one()
    if not active_user_doc:
        return []
    return active_user_doc.active_user

async def get_fullname_by_extension(extension_number: str) -> str:
    active_user_doc = await ActiveUser.find_one()
    if not active_user_doc:
        raise CustomHTTPException(status_code=404, detail="No active user list found")
    for user in active_user_doc.active_user:
        if user.extension_number == extension_number:
            return user.fullname
    raise CustomHTTPException(status_code=404, detail=f"No active user found with extension_number {extension_number}")