import os
import sys
import requests
from pathlib import Path

API_KEY = os.environ.get("PIXABAY_API_KEY")
OUTPUT_FILE = "tiktok_video.mp4"

SEARCH_TERMS = [
    "horror",
    "mystery",
    "dark forest",
    "abandoned house",
    "scary night",
    "mysterious",
]


def main():
    if not API_KEY:
        print("ERROR: PIXABAY_API_KEY is missing.")
        sys.exit(1)

    print("PIXABAY_API_KEY found.")

    selected_video = None

    for term in SEARCH_TERMS:
        print(f"\nSearching Pixabay for: {term}")

        params = {
            "key": API_KEY,
            "q": term,
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

        print(f"Found {len(videos)} videos.")

        if videos:
            videos.sort(
                key=lambda x: (
                    x.get("views", 0),
                    x.get("downloads", 0),
                    x.get("likes", 0),
                ),
                reverse=True,
            )

            selected_video = videos[0]
            break

    if not selected_video:
        print("ERROR: No suitable video found.")
        sys.exit(1)

    print("\nSelected video:")
    print("ID:", selected_video.get("id"))
    print("Views:", selected_video.get("views"))
    print("Downloads:", selected_video.get("downloads"))
    print("Likes:", selected_video.get("likes"))

    video_files = selected_video.get("videos", {})

    video_url = None

    for quality in ["medium", "large", "small"]:
        if quality in video_files:
            video_url = video_files[quality].get("url")
            if video_url:
                break

    if not video_url:
        print("ERROR: No downloadable video found.")
        sys.exit(1)

    print("\nDownloading video...")

    video_response = requests.get(
        video_url,
        timeout=180,
    )

    video_response.raise_for_status()

    Path(OUTPUT_FILE).write_bytes(video_response.content)

    file_size = Path(OUTPUT_FILE).stat().st_size

    print("\n===================================")
    print("VIDEO DOWNLOADED SUCCESSFULLY")
    print("File:", OUTPUT_FILE)
    print("Size:", file_size, "bytes")
    print("===================================")


if __name__ == "__main__":
    main()
