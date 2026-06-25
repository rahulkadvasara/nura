import asyncio
import os
import sys

# Add the backend root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.mongodb import connect_to_mongodb, get_database

async def main():
    await connect_to_mongodb()
    db = get_database()
    cursor = db.doctor_availability.find({})
    docs = await cursor.to_list(length=100)
    print(f"--- Found {len(docs)} availability docs ---")
    for doc in docs:
        print(f"ID: {doc['_id']} | Doctor: {doc.get('doctor_id')} | Date: {doc.get('date')} | Start: {doc.get('start_time')} | End: {doc.get('end_time')} | Active: {doc.get('active')} | Available: {doc.get('is_available')}")

if __name__ == '__main__':
    asyncio.run(main())
