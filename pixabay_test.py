import os
import requests

API_KEY = os.environ.get("PIXABAY_API_KEY")

if not API_KEY:
    raise SystemExit("PIXABAY_API_KEY is missing")

params = {
    "key": API_KEY,
    "q": "horror mystery",
    "video_type": "all",
    "order": "popular",
    "per_page": 10,
    "safesearch": "true",
}

response = requests.get(
    "https://pixabay.com/api/videos/",
    params=params,
    timeout=30,
)

response.raise_for_status()
data = response.json()

hits = data.get("hits", [])

if not hits:
    raise SystemExit("No videos found")

video = hits[0]

print("Found video:")
print("ID:", video.get("id"))
print("Views:", video.get("views"))
print("Downloads:", video.get("downloads"))
print("Likes:", video.get("likes"))

files = video.get("videos", {})

# نختار نسخة HD إذا كانت موجودة
selected = files.get("medium") or files.get("small") or files.get("large")

if not selected:
    raise SystemExit("No downloadable video found")

video_url = selected["url"]

print("Downloading...")

video_response = requests.get(
    video_url,
    timeout=120,
)

video_response.raise_for_status()

with open("test_video.mp4", "wb") as f:
    f.write(video_response.content)

print("DONE!")
print("Saved as test_video.mp4")
