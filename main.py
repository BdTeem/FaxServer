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

import os
import httpx
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()

# এনভায়রনমেন্ট ভেরিয়েবল
MIXDROP_EMAIL = os.environ.get("MIXDROP_EMAIL")
MIXDROP_KEY = os.environ.get("MIXDROP_KEY")

@app.get("/get_mixdrop_link")
async def get_mixdrop_link(file_id: str = Query(..., description="Mixdrop File ID")):
    if not MIXDROP_EMAIL or not MIXDROP_KEY:
        raise HTTPException(status_code=500, detail="Server API configurations missing")

    # এন্ডপয়েন্ট হিসেবে 'info' ব্যবহার করা হচ্ছে যা ডাইরেক্ট লিঙ্ক দেয়
    api_url = f"https://api.mixdrop.ag/info?email={MIXDROP_EMAIL}&key={MIXDROP_KEY}&file_id={file_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url)
            
            # সার্ভার রেসপন্স কোড চেক
            if response.status_code != 200:
                 raise HTTPException(status_code=400, detail=f"Mixdrop Server error: {response.status_code}")

            # JSON ফরম্যাট চেক করা
            try:
                data = response.json()
            except Exception:
                raise HTTPException(status_code=500, detail="Mixdrop returned invalid data format (Not JSON)")
            
            if data.get("success"):
                result_data = data.get("result", {})
                
                # বিভিন্ন নামে লিঙ্ক থাকতে পারে তাই সব চেক করা হচ্ছে
                direct_url = result_data.get("url") or result_data.get("delivery_url") or result_data.get("wurl")
                
                if direct_url:
                    if direct_url.startswith("//"):
                        direct_url = "https:" + direct_url
                    return {"direct_link": direct_url}
                else:
                    raise HTTPException(status_code=404, detail="Direct link not found in Mixdrop response")
            else:
                # মিক্সড্রপ থেকে আসা আসল এরর মেসেজটি দেখানো
                error_msg = data.get("msg") or "Unknown Mixdrop API Error"
                raise HTTPException(status_code=400, detail=f"Mixdrop API says: {error_msg}")
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to Mixdrop: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
