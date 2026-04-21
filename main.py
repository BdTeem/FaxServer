import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse # ✅ এটি যোগ করা হয়েছে
from telethon import TelegramClient
import uvicorn

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = FastAPI()
client = TelegramClient('bot_session', API_ID, API_HASH)

@app.on_event("startup")
async def startup_event():
    await client.start(bot_token=BOT_TOKEN)

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

        # ফাইল পাঠানোর জেনারেটর
        async def file_sender():
            async for chunk in client.iter_download(message.video):
                yield chunk

        # ✅ StreamingResponse ব্যবহার করা হয়েছে যা আপনার এররটি দূর করবে
        return StreamingResponse(file_sender(), media_type="video/mp4")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import os # এটি অবশ্যই থাকতে হবে
import httpx
from fastapi import FastAPI, Query, HTTPException

# ✅ এটি হলো সবচেয়ে সিকিউর পদ্ধতি
MIXDROP_EMAIL = os.environ.get("MIXDROP_EMAIL")
MIXDROP_KEY = os.environ.get("MIXDROP_KEY")

@app.get("/get_mixdrop_link")
async def get_mixdrop_link(file_id: str = Query(..., description="Mixdrop File ID")):
    # যদি সার্ভারে ইমেইল বা কি সেট না থাকে তবে এরর দিবে
    if not MIXDROP_EMAIL or not MIXDROP_KEY:
        raise HTTPException(status_code=500, detail="Server API configurations missing")

    api_url = f"https://api.mixdrop.ag/fileinfo?email={MIXDROP_EMAIL}&key={MIXDROP_KEY}&file={file_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url)
            data = response.json()
            
            if data.get("success"):
                # মিক্সড্রপ থেকে ডাইরেক্ট লিঙ্কটি বের করা
                direct_url = data["result"].get("url")
                if direct_url:
                    # লিঙ্কটি যদি // দিয়ে শুরু হয় তবে https: যোগ করা
                    if direct_url.startswith("//"):
                        direct_url = "https:" + direct_url
                    return {"direct_link": direct_url}
                else:
                    raise HTTPException(status_code=404, detail="Direct link not found")
            else:
                raise HTTPException(status_code=400, detail="Mixdrop API error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
