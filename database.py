# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# import os

# load_dotenv()

# client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
# db = client.chatapp

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.chatapp

users_collection = db["users"]
conversations_collection = db["conversations"]
messages_collection = db["messages"]