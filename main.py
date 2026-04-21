import os
import asyncio
from fastapi import FastAPI, Response, HTTPException
from telethon import TelegramClient
import uvicorn

# এনভায়রনমেন্ট ভেরিয়েবল থেকে ডাটা নেওয়া
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = FastAPI()

# ক্লায়েন্ট তৈরি করা (কিন্তু এখনই start না করা)
client = TelegramClient('bot_session', API_ID, API_HASH)

@app.on_event("startup")
async def startup_event():
    # ✅ সার্ভার শুরু হওয়ার সময় ক্লায়েন্টকে কানেক্ট করা (সঠিক পদ্ধতি)
    await client.start(bot_token=BOT_TOKEN)

@app.get("/")
async def root():
    return {"message": "FaxMovie Server is Running!"}

@app.get("/stream")
async def stream_video(channel: str, msg_id: int):
    try:
        # ✅ সঠিক async হ্যান্ডলিং
        entity = await client.get_entity(channel)
        message = await client.get_messages(entity, ids=msg_id)
        
        if not message or not message.video:
            raise HTTPException(status_code=404, detail="Video not found")

        # ফাইল পাঠানোর ফাংশন
        async def file_sender():
            async for chunk in client.iter_download(message.video):
                yield chunk

        # ভিডিও স্ট্রিমিং রেসপন্স
        return Response(content=file_sender(), media_type="video/mp4")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) # Render এর জন্য সাধারণত ১০হাজার পোর্ট থাকে
    uvicorn.run(app, host="0.0.0.0", port=port)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
