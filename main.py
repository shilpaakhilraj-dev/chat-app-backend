from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, users, chat
from websocket.manager import manager
from database import messages_collection, conversations_collection, users_collection
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import asyncio
import uvicorn
from pydantic import BaseModel

class ReadRequest(BaseModel):
    user_id: str

IST = timezone(timedelta(hours=5, minutes=30))
app = FastAPI()

# ── Presence tracking ─────────────────────────────────────────────────────────
# Maps user_id -> number of open conversation sockets
online_users: dict[str, int] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router, prefix="/api/users")
app.include_router(chat.router, prefix="/api")


# ── IMPORTANT: This route MUST be defined BEFORE /ws/{conversation_id}/{user_id}
# ── Otherwise FastAPI matches "user" as conversation_id and this never runs ──
@app.websocket("/ws/user/{user_id}")
async def user_websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect_user(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)
    except Exception as e:
        print(f"❌ User WS CRASH: {type(e).__name__}: {e}")
        manager.disconnect_user(websocket, user_id)


@app.websocket("/ws/{conversation_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str, user_id: str):
    await manager.connect(websocket, conversation_id)

    # ── Mark user online ──────────────────────────────────────────────────────
    online_users[user_id] = online_users.get(user_id, 0) + 1

    # ── Notify all participants that user came online ──────────────────────────
    await manager.broadcast(
        {"type": "presence", "user_id": user_id, "online": True},
        conversation_id,
    )

    try:
        while True:
            data = await websocket.receive_json()
            now = datetime.now(IST)
            msg = {
                "conversation_id": str(conversation_id),
                "sender_id": user_id,
                "text": data["text"],
                "timestamp": now.isoformat(),
                "is_read": False,
            }
            result = await messages_collection.insert_one({**msg, "timestamp": now})
            msg["_id"] = str(result.inserted_id)

            await conversations_collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"lastMessage": data["text"], "lastTime": now}}
            )

            await manager.broadcast(msg, conversation_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
        await _handle_disconnect(user_id, conversation_id)
    except Exception as e:
        print(f"❌ CRASH: {type(e).__name__}: {e}")
        manager.disconnect(websocket, conversation_id)
        await _handle_disconnect(user_id, conversation_id)


async def _handle_disconnect(user_id: str, conversation_id: str):
    """Decrement socket count, save last_seen, and broadcast offline if last socket closed."""
    online_users[user_id] = online_users.get(user_id, 1) - 1

    if online_users[user_id] <= 0:
        online_users.pop(user_id, None)
        last_seen_time = datetime.now(IST).isoformat()

        # ── Save last_seen to DB ──────────────────────────────────────────────
        try:
            await users_collection.update_one(
                {"_id": user_id},
                {"$set": {"last_seen": last_seen_time}}
            )
        except Exception as e:
            print(f"⚠️ Failed to save last_seen for {user_id}: {e}")

        # ── Broadcast offline + last_seen to conversation participants ─────────
        await manager.broadcast(
            {
                "type": "presence",
                "user_id": user_id,
                "online": False,
                "last_seen": last_seen_time,
            },
            conversation_id,
        )
    else:
        print(f"🟡 {user_id} still online (sockets: {online_users[user_id]})")


# ── REST fallback: poll-based status + last_seen ──────────────────────────────
@app.get("/api/users/{user_id}/status")
async def get_user_status(user_id: str):
    is_online = user_id in online_users
    last_seen = None

    if not is_online:
        # ── Fetch last_seen from DB only when offline ─────────────────────────
        try:
            user = await users_collection.find_one({"_id": user_id})
            last_seen = user.get("last_seen") if user else None
        except Exception as e:
            print(f"⚠️ Failed to fetch last_seen for {user_id}: {e}")

    return {
        "user_id": user_id,
        "online": is_online,
        "last_seen": last_seen,
    }

@app.put("/api/conversations/{conversation_id}/read")
async def mark_messages_as_read(conversation_id: str, payload: ReadRequest):
    """Marks all messages in a conversation as read by the specified user"""
    # Find all messages in this conversation where sender is NOT the current user
    # and mark them as is_read: True
    await messages_collection.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": payload.user_id},
            "is_read": {"$ne": True}
        },
        {"$set": {"is_read": True}}
    )
    return {"status": "success", "message": "Messages marked as read"}


@app.get("/")
async def root():
    return {"message": "Chat API is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)