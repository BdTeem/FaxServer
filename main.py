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

app = FastAPI() # এই লাইনটি কোডে থাকতে হবে

MIXDROP_EMAIL = os.environ.get("MIXDROP_EMAIL")
MIXDROP_KEY = os.environ.get("MIXDROP_KEY")

@app.get("/get_mixdrop_link")
async def get_mixdrop_link(file_id: str = Query(..., description="Mixdrop File ID")):
    if not MIXDROP_EMAIL or not MIXDROP_KEY:
        raise HTTPException(status_code=500, detail="Server API configurations missing")

    # ✅ 'fileinfo' এর বদলে 'info' ব্যবহার করুন এবং '&file=' এর বদলে '&file_id=' দিন
    api_url = f"https://api.mixdrop.ag/info?email={MIXDROP_EMAIL}&key={MIXDROP_KEY}&file_id={file_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url)
            data = response.json()
            
            # মিক্সড্রপ এপিআই সফল হলে এটি 'success' হিসেবে থাকে
            if data.get("success"):
                # মিক্সড্রপ অনেক সময় 'result' এর ভেতর 'url' দেয়, 
                # কিছু ক্ষেত্রে এটি 'fileref' এর ভেতরেও থাকতে পারে
                result_data = data.get("result", {})
                
                # আমরা সব ধরণের সম্ভাবনা চেক করছি যেন এরর না আসে
                direct_url = result_data.get("url") or result_data.get("delivery_url")
                
                if direct_url:
                    if direct_url.startswith("//"):
                        direct_url = "https:" + direct_url
                    return {"direct_link": direct_url}
                else:
                    raise HTTPException(status_code=404, detail="Direct link not found in response")
            else:
                # যদি মিক্সড্রপ রিফিউজ করে, তবে আসল কারণটি দেখতে পাবেন
                raise HTTPException(status_code=400, detail=f"Mixdrop Error: {data.get('msg', 'Unknown Error')}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
