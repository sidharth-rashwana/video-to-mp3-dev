from celery import Celery
from moviepy.editor import VideoFileClip
from app.server.logger.custom_logger import logger
import os

redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
CELERY_PATH = os.getenv("CELERY_PATH", "/tmp/celery")

app = Celery(__name__, broker=redis_url, backend=redis_url)

def ensure_folder():
    os.makedirs(CELERY_PATH, exist_ok=True)
    return CELERY_PATH

@app.task
def convert_mp4_to_mp3(filename, content):
    folder = os.getenv("CELERY_PATH", "/tmp/celery")
    os.makedirs(folder, exist_ok=True)

    input_path = os.path.join(folder, filename)
    output_path = os.path.join(folder, f"{os.path.splitext(filename)[0]}.mp3")

    try:
        with open(input_path, "wb") as f:
            f.write(content)

        video_clip = VideoFileClip(input_path)
        audio_clip = video_clip.audio

        if audio_clip is None:
            logger.error("❌ No audio track found in the video.")
            return {"error": "No audio track found in video"}

        audio_clip.write_audiofile(output_path)

        return {"output_path": output_path}

    except Exception as e:
        logger.exception("Error in convert_mp4_to_mp3")
        return {"error": str(e)}

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.task
def extract_audio_section_from_video(filename, content, start_time, end_time):
    folder = ensure_folder()
    input_path = os.path.join(folder, filename)
    output_filename = f"{os.path.splitext(filename)[0]}_section.mp3"
    output_path = os.path.join(folder, output_filename)

    try:
        with open(input_path, "wb") as f:
            f.write(content)

        video_clip = VideoFileClip(input_path)
        audio_clip = video_clip.audio

        if start_time >= end_time or end_time > video_clip.duration or start_time < 0:
            raise ValueError("Invalid start_time or end_time provided.")

        audio_section = audio_clip.subclip(start_time, end_time)
        audio_section.write_audiofile(output_path)

        return {"output_path": output_path}

    except Exception as e:
        logger.exception("Error in extract_audio_section_from_video")
        raise e

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
