import os
import sys
import subprocess
import requests
from pathlib import Path

API_KEY = os.environ.get("PIXABAY_API_KEY")

OUTPUT_FILE = "tiktok_story.mp4"

SCENES = [
    "abandoned house night",
    "woman walking dark hallway",
    "old door night",
    "dark room mysterious",
    "shadow person",
    "scared woman night",
]

SCENE_DURATION = 5


def run_command(command):
    subprocess.run(command, check=True)


def search_video(query):
    print(f"\nSearching: {query}")

    params = {
        "key": API_KEY,
        "q": query,
        "video_type": "all",
        "order": "popular",
        "per_page": 20,
        "safesearch": "true",
    }

    response = requests.get(
        "https://pixabay.com/api/videos/",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    videos = response.json().get("hits", [])

    if not videos:
        print("No videos found.")
        return None

    videos.sort(
        key=lambda x: (
            x.get("views", 0),
            x.get("downloads", 0),
            x.get("likes", 0),
        ),
        reverse=True,
    )

    return videos[0]


def get_video_url(video):
    files = video.get("videos", {})

    for quality in ["medium", "large", "small"]:
        if quality in files:
            url = files[quality].get("url")
            if url:
                return url

    return None


def download_video(url, filename):
    print(f"Downloading {filename}...")

    response = requests.get(
        url,
        timeout=180,
    )

    response.raise_for_status()

    Path(filename).write_bytes(response.content)


def prepare_scene(input_file, output_file):
    print(f"Preparing {input_file}...")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-t",
        str(SCENE_DURATION),
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "fps=30",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        output_file,
    ]

    run_command(command)


def create_story_video(files):
    print("\nCreating story video...")

    prepared_files = []

    for index, filename in enumerate(files, start=1):
        prepared = f"prepared_{index}.mp4"

        prepare_scene(filename, prepared)

        prepared_files.append(prepared)

    list_file = Path("videos.txt")

    with list_file.open("w", encoding="utf-8") as f:
        for filename in prepared_files:
            absolute_path = Path(filename).absolute()
            f.write(f"file '{absolute_path}'\n")

    print("\nJoining scenes...")

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "videos.txt",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        OUTPUT_FILE,
    ]

    run_command(command)

    print("\n================================")
    print("STORY VIDEO CREATED")
    print("File:", OUTPUT_FILE)
    print("Duration: about 30 seconds")
    print("================================")


def main():
    if not API_KEY:
        print("ERROR: PIXABAY_API_KEY is missing.")
        sys.exit(1)

    print("PIXABAY_API_KEY found.")

    downloaded_files = []

    for index, scene in enumerate(SCENES, start=1):

        print(f"\n========== SCENE {index} ==========")

        video = search_video(scene)

        if not video:
            continue

        print("Selected ID:", video.get("id"))
        print("Views:", video.get("views"))

        url = get_video_url(video)

        if not url:
            print("No downloadable file.")
            continue

        filename = f"scene_{index}.mp4"

        download_video(url, filename)

        downloaded_files.append(filename)

    if len(downloaded_files) < 2:
        print("ERROR: Not enough scenes found.")
        sys.exit(1)

    create_story_video(downloaded_files)


if __name__ == "__main__":
    main()
