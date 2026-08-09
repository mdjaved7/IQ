import os
import asyncio
import subprocess
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.video | filters.document)
async def process_video(client, message):
    status_msg = await message.reply_text("🔄 Video download ki ja rahi hai...")
    
    video_path = await message.download()
    await status_msg.edit_text("⚙️ Video par watermark lagakar cut kiya ja raha hai...")
    
    output_pattern = f"output_{message.chat.id}_%03d.mp4"
    
    # Yahan '-map 0:a?' use kiya gaya hai taaki agar video me sound na ho tab bhi error na aaye
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-i", "logo.png", "-i", "watermark.png",
        "-filter_complex", "[0:v][1:v]overlay=10:10[v1];[v1][2:v]overlay=(W-w)/2:(H-h)/2[outv]",
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
        "-f", "segment", "-segment_time", "900", "-reset_timestamps", "1",
        output_pattern
    ]
    
    process = await asyncio.create_subprocess_exec(*ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_text = stderr.decode()[-400:]
        await status_msg.edit_text(f"❌ FFmpeg Error aaya:\n`{error_text}`", parse_mode="markdown")
        if os.path.exists(video_path):
            os.remove(video_path)
        return

    await status_msg.edit_text("📤 Sabhi parts upload kiye ja rahe hain...")
    output_files = sorted([f for f in os.listdir() if f.startswith(f"output_{message.chat.id}_")])
    
    for file in output_files:
        await message.reply_video(video=file, caption=f"✅ Part: {file}")
        await asyncio.sleep(2)
        
    if os.path.exists(video_path):
        os.remove(video_path)
    for file in output_files:
        if os.path.exists(file):
            os.remove(file)
            
    await status_msg.delete()

print("Bot started...")
app.run()
