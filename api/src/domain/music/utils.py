import os
import re
import time
from io import BytesIO

import yt_dlp

from api.src.domain.music.schemas import FileDTO
from api.src.infrastructure.settings import settings


download_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "youtube_downloads"
)
os.makedirs(download_dir, exist_ok=True)


def clean_title(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", title.replace("/", "-").strip())


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
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",  # ← This extracts audio
                "preferredcodec": "m4a",  # ← Output as .m4a
                "preferredquality": "0",  # 0 лучшее качество
            }
        ],
        'extractor_args': {
            'youtube': {
                'player_skip': ['configs', 'webpage'],
                'force_key': ['api_key', 'visitor_data'],  # Added visitor_data
                'api_key': settings.youtube.api_key,
                'visitor_data': settings.youtube.visitor_info1_live,
            },
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        'force_generic_extractor': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            time.sleep(5)
        except yt_dlp.utils.DownloadError as e:
            print(f"Ошибка загрузки: {e}")
            return None

    time.sleep(2)
    local_file_path = os.path.join(download_dir, f"{info['id']}.m4a")
    with open(local_file_path, "rb") as file:
        audio_data = BytesIO(file.read())
    audio_data.seek(0)
    os.remove(local_file_path)

    return FileDTO(
        data=audio_data,
        title=info["title"],
        filename=clean_title(f"{info['title']} [{info['id']}].m4a"),
        duration=float(info["duration_string"].replace(":", ".")),
    )


def get_audio_data_from_youtube(url: str) -> FileDTO:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return FileDTO(
        title=info["title"],
        filename=clean_title(
            f"{info['title']} [{info['id']}].{info.get('audio_ext', 'm4a')}"
        ),
        duration=convert_str_duration_to_float(info["duration_string"]),
    )
