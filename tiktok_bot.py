import os
import sys
import json
import base64
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests
from google import genai
from google.genai import types

# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.8-flash")
VIDEO_MODEL = os.getenv("GEMINI_VIDEO_MODEL", "gemini-omni-1.1-flash")
TREND_GEO = os.getenv("TREND_GEO", "US")
OUTPUT_VIDEO = "tiktok_video.mp4"
OUTPUT_METADATA = "video_metadata.json"

# One optional extension creates a longer video (up to 20 seconds).
# Set VIDEO_EXTENSIONS=0 to generate a single 3-10 second clip.
VIDEO_EXTENSIONS = int(os.getenv("VIDEO_EXTENSIONS", "1"))

FALLBACK_CATEGORIES = [
    "surreal AI transformations",
    "impossible satisfying processes",
    "cinematic fantasy worlds",
    "photorealistic animals doing unexpected things",
    "futuristic inventions and places",
    "tiny worlds and miniature scenes",
    "visual optical illusions",
    "before-and-after transformations",
    "unexpected food and object transformations",
    "dreamlike nature and space scenes",
]

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY secret is missing.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# TREND SIGNALS
# ============================================================

def get_google_trends():
    """
    Fetches Google Trends' public trending-search RSS feed.
    This is a trend signal, NOT TikTok's private/internal trending data.
    """
    url = f"https://trends.google.com/trending/rss?geo={TREND_GEO}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TrendResearchBot/1.0)"}

    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = []

        for item in root.findall(".//item")[:15]:
            title = item.findtext("title", default="").strip()
            traffic = item.findtext("{https://trends.google.com/trending/rss}approx_traffic", default="")
            if title:
                items.append({"topic": title, "approx_traffic": traffic})

        return items
    except Exception as exc:
        print(f"Trend RSS unavailable; using broad AI-video categories. Details: {exc}")
        return []


def choose_trend_brief(trends):
    if trends:
        trend_lines = "\n".join(
            f"- {x['topic']} (approx. search traffic: {x['approx_traffic'] or 'not provided'})"
            for x in trends
        )
        source_note = (
            f"Use these current Google Trends search signals for {TREND_GEO} as inspiration. "
            "Do not force an unrelated trend into the video."
        )
    else:
        trend_lines = "\n".join(f"- {x}" for x in FALLBACK_CATEGORIES)
        source_note = (
            "Live trend data was unavailable. Choose one broadly appealing AI-video concept "
            "from these categories; do not claim it is currently trending."
        )

    prompt = f"""
You are the creative director of a high-quality AI short-video channel.
The channel publishes ONE original AI-generated vertical video per day.
The content mix is broad: surreal, cinematic, satisfying, funny, futuristic,
animals, transformations, visual illusions, fantasy, food, nature and other
visually compelling formats. Do not make every video a story.

TREND SIGNALS:
{trend_lines}

{source_note}

Create one original, highly visual concept suitable for TikTok/Reels/Shorts.
Prioritize an immediate visual hook in the first second, a clear visual payoff,
strong motion, and a loopable or surprising ending.
Do not copy a creator's exact video, copyrighted characters, logos, or a specific
living artist's style. Do not include dangerous stunts or misleading real-world claims.
Avoid relying on readable text inside the generated video.

Return ONLY valid JSON with this exact structure:
{{
  "title": "short internal title",
  "format": "e.g. surreal transformation / satisfying / cinematic fantasy",
  "trend_basis": "which signal inspired the idea, or say broad evergreen concept",
  "concept": "one-sentence description",
  "video_prompt": "detailed generation prompt for a 9:16 video, with clear subject motion, camera direction, lighting, environment, visual style, and natural audio",
  "caption": "short TikTok caption",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}

The video prompt should describe one coherent 10-second clip that can be extended
once. Make it visually understandable without narration or subtitles.
"""

    result = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        idea = json.loads(result.text)
    except Exception as exc:
        raise RuntimeError(f"Gemini did not return valid JSON: {result.text}") from exc

    required = ["title", "format", "concept", "video_prompt", "caption", "hashtags"]
    missing = [key for key in required if not idea.get(key)]
    if missing:
        raise RuntimeError(f"Gemini response is missing fields: {missing}")

    if not isinstance(idea["hashtags"], list):
        raise RuntimeError("hashtags must be a JSON list")

    return idea, trends


# ============================================================
# VIDEO GENERATION
# ============================================================

def save_video_output(interaction, path):
    output = getattr(interaction, "output_video", None)
    data = getattr(output, "data", None) if output else None

    if not data:
        uri = getattr(output, "uri", None) if output else None
        if uri:
            raise RuntimeError(
                "The video API returned a hosted URI instead of inline video data. "
                "URI download handling needs to be enabled for this account/response."
            )
        raise RuntimeError("Gemini Omni returned no video data.")

    # SDK output_video.data is base64-encoded according to the Gemini API docs.
    if isinstance(data, str):
        video_bytes = base64.b64decode(data)
    else:
        video_bytes = bytes(data)

    with open(path, "wb") as file:
        file.write(video_bytes)

    if os.path.getsize(path) < 10_000:
        raise RuntimeError("Generated video file is unexpectedly small.")


def generate_video(prompt, output_path):
    print(f"Generating video with {VIDEO_MODEL}...")

    interaction = client.interactions.create(
        model=VIDEO_MODEL,
        input=prompt,
        response_format={
            "type": "video",
            "aspect_ratio": "9:16",
            "resolution": "720p",
        },
    )

    save_video_output(interaction, output_path)

    # Optional conversational extension. Each extension adds up to 10 seconds.
    previous_id = getattr(interaction, "id", None)

    for extension_number in range(VIDEO_EXTENSIONS):
        if not previous_id:
            print("No interaction ID returned; skipping video extension.")
            break

        print(f"Extending video ({extension_number + 1}/{VIDEO_EXTENSIONS})...")
        extension = client.interactions.create(
            model=VIDEO_MODEL,
            previous_interaction_id=previous_id,
            input=(
                "Continue this exact video seamlessly for up to 10 more seconds. "
                "Preserve the same subject, visual identity, environment, motion logic, "
                "lighting and audio mood. Add a fresh visual development and finish "
                "with a satisfying, memorable, loop-friendly ending. Keep it vertical 9:16."
            ),
            response_format={
                "type": "video",
                "aspect_ratio": "9:16",
                "resolution": "720p",
            },
        )

        # Use the latest interaction's returned video as the final deliverable.
        # The API's multi-turn result represents the edited/continued video state.
        save_video_output(extension, output_path)
        previous_id = getattr(extension, "id", None)

    print(f"Video saved: {output_path}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 58)
    print("             AI VIRAL VIDEO BOT")
    print("=" * 58)

    trends = get_google_trends()
    print(f"Trend signals collected: {len(trends)}")

    idea, trends = choose_trend_brief(trends)

    print("\nSelected concept:")
    print(json.dumps(idea, ensure_ascii=False, indent=2))

    generate_video(idea["video_prompt"], OUTPUT_VIDEO)

    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "trend_geo": TREND_GEO,
        "trend_source": "Google Trends RSS (search-interest signal, not TikTok analytics)",
        "trend_signals": trends,
        "idea": idea,
        "video_file": OUTPUT_VIDEO,
        "publishing_status": "REVIEW_REQUIRED",
    }

    with open(OUTPUT_METADATA, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("\nDONE.")
    print(f"Video: {OUTPUT_VIDEO}")
    print(f"Metadata: {OUTPUT_METADATA}")
    print("Publishing is intentionally not automatic. Review the video first.")


if __name__ == "__main__":
    main()
