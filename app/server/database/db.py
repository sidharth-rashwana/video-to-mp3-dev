import motor.motor_asyncio
from app.server.config import environment

client = motor.motor_asyncio.AsyncIOMotorClient(environment.MONGO_URI)

mongo = client.get_database()