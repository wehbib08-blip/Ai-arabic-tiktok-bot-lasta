import os
import sys
import requests
from pathlib import Path

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

OUTPUT_FILE = "tiktok_video.mp4"

SEARCH_TERMS = [
    "horror",
    "mystery",
    "dark forest",
    "abandoned house",
    "scary night",
    "mysterious",
]

def check_key():
    if not PIXABAY_API_KEY:
        print("ERROR: PIXABAY_API_KEY is missing.")
        sys.exit(1)

    print("PIXABAY_API_KEY found.")


def search_pixabay(query):
    print(f"\nSearching Pixabay for: {query}")

    params = {
        "key": PIXABAY_API_KEY,
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
   
