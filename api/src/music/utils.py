import os
import re
from io import BytesIO

import yt_dlp
from api.src.music.schemas import FileDTO


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
        # 'quiet': True,
        # 'no_warnings': True,
        'noplaylist': True,
        # 'noprogress': True,
        'format': 'm4a/bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s',
        "force_ipv4": True,
        "source_address": "0.0.0.0",
        "retries": 3,
        "fragment_retries": 3,
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        # 'postprocessors': [{  # Extract audio using ffmpeg
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'wav',
        # }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    local_file_path = f"{info['id']}.{info['audio_ext']}"
    with open(local_file_path, "rb") as file:
        audio_data = BytesIO(file.read())
    audio_data.seek(0)
    os.remove(local_file_path)

    return FileDTO(
        data=audio_data,
        title=info['title'],
        filename=clean_title(f"{info['title']} [{info['id']}].m4a"),
        duration=float(info["duration_string"].replace(":", "."))
    )


def get_audio_data_from_youtube(url: str) -> FileDTO:
    ydl_opts = {
        # 'quiet': True,
        # 'no_warnings': True,
        'skip_download': True,
        # 'extract_flat': True,
        'noplaylist': True,
        # 'noprogress': True,
        # 'extractor_args': {
        #     'youtube': {'player_skip': ['webpage', 'js', 'initial_data'],
        #                 },
        # },
        # "dynamic_mpd": False,
        # "clean_infojson": False,
        # "lazy_playlist": True,

    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return FileDTO(
        title=info['title'],
        filename=clean_title(f"{info['title']} [{info['id']}].m4a"),
        duration=convert_str_duration_to_float(info["duration_string"])
    )
