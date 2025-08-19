import os
import re
from io import BytesIO

import yt_dlp

from api.src.domain.music.schemas import FileDTO


def clean_title(title: str) -> str:
    return re.sub(
        r'[<>:"/\\|?*]',
        '',
        title.replace("/", "-").strip()
    )


def convert_str_duration_to_float(duration: str) -> float:
    # нужно оптимизировать!!!!
    dur_lst: list = list(map(int, duration.replace(":", ".").split(".")))
    if len(dur_lst) > 2:
        result = float(f"{(dur_lst[0] * 60) + dur_lst[1]}.{dur_lst[2]}")
    else:
        result = float(duration.replace(":", "."))
    return result


def download_audio_from_youtube(url: str) -> FileDTO:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'format': ' m4a/bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as e:
            print(f"Ошибка загрузки: {e}")
            return None

    audio_ext = info.get('audio_ext', 'm4a')
    local_file_path = f"{info['id']}.{audio_ext}"
    with open(local_file_path, "rb") as file:
        audio_data = BytesIO(file.read())
    audio_data.seek(0)
    os.remove(local_file_path)

    return FileDTO(
        data=audio_data,
        title=info['title'],
        filename=clean_title(f"{info['title']} [{info['id']}].{audio_ext}"),
        duration=float(info["duration_string"].replace(":", "."))
    )


def get_audio_data_from_youtube(url: str) -> FileDTO:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return FileDTO(
        title=info['title'],
        filename=clean_title(f"{info['title']} [{info['id']}].{info.get('audio_ext', 'm4a')}"),
        duration=convert_str_duration_to_float(info["duration_string"])
    )
