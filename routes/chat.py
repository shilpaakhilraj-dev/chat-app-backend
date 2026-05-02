from fastapi import APIRouter, HTTPException
from database import conversations_collection, messages_collection
from models.conversation import ConversationModel
from models.message import MessageModel
from bson import ObjectId
from datetime import datetime
from websocket.manager import manager

router = APIRouter()

@router.get("/conversations")
async def get_conversations(user_id: str):
    cursor = conversations_collection.find({"participants.id": user_id})
    conversations = []
    async for conv in cursor:
        conv["_id"] = str(conv["_id"])
        conversations.append(conv)
    return conversations

@router.post("/conversations")
async def create_conversation(data: ConversationModel):
    participant_ids = [p.id for p in data.participants]

    existing = await conversations_collection.find_one(
        {"participants.id": {"$all": participant_ids}}
    )
    if existing:
        existing["_id"] = str(existing["_id"])
        return existing

    result = await conversations_collection.insert_one({
        "participants": [p.dict() for p in data.participants],
        "lastMessage": "",
        "lastTime": datetime.utcnow()
    })

    conv_id = str(result.inserted_id)
    participants_data = [p.dict() for p in data.participants]

    # ── Notify each participant via their user-level WebSocket ────────────────
    conv_payload = {
        "type": "new_conversation",
        "conversation": {
            "_id": conv_id,
            "participants": participants_data,
            "lastMessage": "",
            "lastTime": None,
        }
    }
    for participant in participants_data:
        await manager.notify_user(participant["id"], conv_payload)

    return {"_id": conv_id, "participants": data.participants}

@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str):
    cursor = messages_collection.find({"conversation_id": conv_id}).sort("timestamp", 1)
    messages = []
    async for msg in cursor:
        msg["_id"] = str(msg["_id"])
        messages.append(msg)
    return messages

@router.post("/messages")
async def send_message(data: MessageModel):
    msg = data.dict()
    msg["timestamp"] = datetime.utcnow()
    result = await messages_collection.insert_one(msg)

    # Update last message in conversation
    await conversations_collection.update_one(
        {"_id": ObjectId(data.conversation_id)},
        {"$set": {"lastMessage": data.text, "lastTime": datetime.utcnow()}}
    )

    msg["_id"] = str(result.inserted_id)
    return msg