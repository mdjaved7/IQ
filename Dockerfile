# Python ka official image use karein
FROM python:3.12-slim

# System dependencies (FFmpeg aur GCC) install karein
RUN apt-get update && apt-get install -y ffmpeg gcc python3-dev

# Kaam karne ki jagah (Working Directory)
WORKDIR /app

# Files ko folder mein copy karein
COPY . .

# Python libraries install karein
RUN pip install --no-cache-dir -r requirements.txt

# Bot start karein
CMD ["python", "bot.py"]
