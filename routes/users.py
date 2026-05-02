from fastapi import APIRouter, Query
from database import users_collection, conversations_collection

router = APIRouter()

@router.get("/find")
async def find_user(email: str = Query(...), requester_id: str = Query(None)):
    user = await users_collection.find_one({"email": email})
    if not user:
        return {"user": None}

    found_user = {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "already_chatting": False,
    }

    # If requester_id is provided, check if a conversation already exists
    if requester_id:
        existing_conv = await conversations_collection.find_one({
            "participants.id": {"$all": [requester_id, str(user["_id"])]}
        })
        if existing_conv:
            found_user["already_chatting"] = True
            found_user["conversation_id"] = str(existing_conv["_id"])

    return {"user": found_user}