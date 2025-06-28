import os
from io import BytesIO
import yt_dlp
import re
import time


def download_audio_from_youtube(url: str) -> dict:
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s',
        'noplaylist': True,
        "quiet": True, # отключает логи статуса загруски
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        # 'postprocessors': [{  # Extract audio using ffmpeg
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'wav',
        # }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # stream = info["url"]

    local_file_path = f"{info['id']}.{info['audio_ext']}"
    with open(local_file_path, "rb") as file:
        audio_data = BytesIO(file.read())
    audio_data.seek(0)
    os.remove(local_file_path)
    time.sleep(10)
    # уберает опасные символы
    file_name = re.sub(
        r'[<>:"/\\|?*]',
        '',
        f"{info['title']} [{info['id']}].{info['audio_ext']}".replace("/", "-").strip()
    )

    return {"data": audio_data, "title": info['title'], "filename": file_name}
