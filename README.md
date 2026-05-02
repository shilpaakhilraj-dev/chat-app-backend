# Real-Time Chat Application (FastAPI + WebSockets)

A scalable real-time chat backend built using **FastAPI**, **WebSockets**, and **MongoDB**. This application supports user authentication, real-time messaging, conversation management, and online/offline presence tracking.

---

## Features

* 🔐 User Authentication (JWT-based)
* 💬 Real-time messaging using WebSockets
* 👥 One-to-one conversation support
* 🟢 Online / Offline presence tracking
* ⏱ Last seen functionality
* 📩 Message read receipts
* 🔎 User search & chat initiation
* ⚡ FastAPI async architecture for high performance

---

## Project Structure

```
.
├── main.py              # Application entry point
├── database.py          # MongoDB connection setup
├── routes/
│   ├── auth.py          # Authentication APIs
│   ├── users.py         # User search APIs
│   └── chat.py          # Chat & conversation APIs
├── websocket/
│   └── manager.py       # WebSocket connection manager
├── models/              # Pydantic models (user, message, conversation)
└── .env                 # Environment variables
```

---

## Tech Stack

* **Backend**: FastAPI
* **Database**: MongoDB (Motor - async driver)
* **Authentication**: JWT (python-jose)
* **Password Hashing**: Passlib (bcrypt)
* **Realtime**: WebSockets
* **Server**: Uvicorn

---

## Key Concepts

### Presence Tracking

* Tracks active WebSocket connections per user
* Marks users online/offline dynamically
* Stores `last_seen` in database

### Message Flow

1. Client sends message via WebSocket
2. Message stored in MongoDB
3. Broadcast to all participants
4. Conversation updated with last message

### Read Receipts

* Messages marked as read when user opens conversation
* Only updates messages not sent by current user

---

## Author

Developed as a real-time chat backend using modern async Python architecture.

---

## 📄 License

This project is open-source and available under the MIT License.

---
