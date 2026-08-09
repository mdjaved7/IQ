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
    status_msg = await message.reply_text("🔄 Video download ki ja rahi hai, kripya intezar karein...")
    
    video_path = await message.download()
    await status_msg.edit_text("⚙️ Step 1: Video par logo aur watermark lagaya ja raha hai...")
    
    processed_video = f"processed_{message.chat.id}.mp4"
    
    # Step 1: Watermark apply karne ki safe command (fixed keyframes ke sath)
    watermark_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-i", "logo.png", "-i", "watermark.png",
        "-filter_complex", "[0:v][1:v]overlay=10:10[v1];[v1][2:v]overlay=(W-w)/2:(H-h)/2[outv]",
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        processed_video
    ]
    
    process = await asyncio.create_subprocess_exec(*watermark_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_text = stderr.decode()[-300:]
        await status_msg.edit_text(f"❌ Watermark Error:\n{error_text}")
        if os.path.exists(video_path): 
            os.remove(video_path)
        return

    await status_msg.edit_text("✂️ Step 2: Video ko 15-15 minute ke parts mein cut kiya ja raha hai...")
    
    # Step 2: Parts mein split karne ki command
    output_pattern = f"output_{message.chat.id}_%03d.mp4"
    split_cmd = [
        "ffmpeg", "-y", "-i", processed_video,
        "-c", "copy",
        "-f", "segment", "-segment_time", "900", "-reset_timestamps", "1",
        output_pattern
    ]
    
    process2 = await asyncio.create_subprocess_exec(*split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout2, stderr2 = await process2.communicate()
    
    if process2.returncode != 0:
        error_text = stderr2.decode()[-300:]
        await status_msg.edit_text(f"❌ Split Error:\n{error_text}")
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(processed_video): os.remove(processed_video)
        return

    await status_msg.edit_text("📤 Sabhi parts upload kiye ja rahe hain...")
    output_files = sorted([f for f in os.listdir() if f.startswith(f"output_{message.chat.id}_")])
    
    if not output_files:
        await status_msg.edit_text("❌ Error: Koi output file generate nahi hui!")
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(processed_video): os.remove(processed_video)
        return

    for file in output_files:
        await message.reply_video(video=file, caption=f"✅ Part: {file}")
        await asyncio.sleep(2)
        
    # Safai (Files delete karna taaki server full na ho)
    if os.path.exists(video_path): os.remove(video_path)
    if os.path.exists(processed_video): os.remove(processed_video)
    for file in output_files:
        if os.path.exists(file): os.remove(file)
            
    await status_msg.delete()

print("Bot started...")
app.run()
