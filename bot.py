import subprocess
import sys

# Pella panel ke liye automatic dependency installer
def install_dependencies():
    packages = ["pyrogram==2.0.106", "tgcrypto", "imageio-ffmpeg"]
    for package in packages:
        import_name = package.split("==")[0].replace("-", "_")
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

import os
import asyncio
from pyrogram import Client, filters
import imageio_ffmpeg

# Yahan apni API ID, API Hash aur Bot Token dalein
API_ID = 34801155  
API_HASH = "d7846c4d0f2c343dd5b67c80d45409e8"
BOT_TOKEN = "8675595326:AAFmFGYXweatDVWYU3fRHqSHLqgg-4LWOkw"

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

app = Client(
    "video_watermark_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.video | filters.document)
async def process_video(client, message):
    status_msg = await message.reply_text("🔄 Video download ki ja rahi hai, kripya intezar karein...")
    
    video_path = await message.download()
    await status_msg.edit_text("⚙️ Video par logo, watermark lagakar 15-15 minute ke parts mein cut kiya ja raha hai...")
    
    output_pattern = f"output_{message.chat.id}_%03d.mp4"
    
    ffmpeg_cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-i", "logo.png",
        "-i", "watermark.png",
        "-filter_complex", "[0:v][1:v]overlay=10:10[v1];[v1][2:v]overlay=(W-w)/2:(H-h)/2[outv]",
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-f", "segment",
        "-segment_time", "900",
        "-reset_timestamps", "1",
        output_pattern
    ]
    
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        await status_msg.edit_text(f"❌ Processing mein error aaya:\n{stderr.decode()[-400:]}")
        if os.path.exists(video_path):
            os.remove(video_path)
        return

    await status_msg.edit_text("📤 Sabhi parts upload kiye ja rahe hain...")
    
    output_files = sorted([f for f in os.listdir() if f.startswith(f"output_{message.chat.id}_")])
    
    for file in output_files:
        await message.reply_video(
            video=file, 
            caption=f"✅ Part: {file}"
        )
        await asyncio.sleep(3)
        
    await status_msg.edit_text("🎉 Sabhi parts successfully bhej diye gaye hain!")
    
    if os.path.exists(video_path):
        os.remove(video_path)
    for file in output_files:
        if os.path.exists(file):
            os.remove(file)

print("Bot started...")
app.run()
