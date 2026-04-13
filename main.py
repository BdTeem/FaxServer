import os
from fastapi import FastAPI, Response, HTTPException
from telethon import TelegramClient
import uvicorn

# --- এখান থেকে নিরাপদ পদ্ধতি শুরু ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# --- শেষ ---

app = FastAPI()
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@app.get("/")
async def root():
    return {"message": "FaxMovie Server is Running!"}

@app.get("/stream")
async def stream_video(channel: str, msg_id: int):
    try:
        entity = await client.get_entity(channel)
        message = await client.get_messages(entity, ids=msg_id)
        
        if not message or not message.video:
            raise HTTPException(status_code=404, detail="Video not found")

        async def file_sender():
            async for chunk in client.iter_download(message.video):
                yield chunk

        return Response(content=file_sender(), media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
