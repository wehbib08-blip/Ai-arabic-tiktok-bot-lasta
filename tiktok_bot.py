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

# Alternate the two content pillars daily (same UTC date = same category).
TODAY_UTC = datetime.now(timezone.utc).date()
DAILY_CATEGORY = "FUNNY_AI" if TODAY_UTC.toordinal() % 2 == 0 else "SATISFYING"

# One optional extension creates a longer video (up to 20 seconds).
# Set VIDEO_EXTENSIONS=0 to generate a single 3-10 second clip.
VIDEO_EXTENSIONS = int(os.getenv("VIDEO_EXTENSIONS", "1"))

FALLBACK_CATEGORIES = [
    "Funny AI: absurd visual comedy with a strong punchline",
    "Satisfying: tactile, hypnotic visual processes with crisp ASMR-style sound",
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
You are the creative director of a premium viral AI short-video channel.
The channel publishes ONE original vertical video per day. The ONLY two content
pillars are Funny AI and Satisfying. Today's required pillar is: {DAILY_CATEGORY}.

CATEGORY RULES:
- If today's pillar is FUNNY_AI: create a genuinely funny visual AI comedy gag.
  Use an unexpected but instantly understandable situation, expressive characters
  or photorealistic animals, excellent comic timing, escalating absurdity, and a
  clear visual punchline. No generic cute montage, no slow intro, no random cuts.
  The joke must be understandable with the sound off.
- If today's pillar is SATISFYING: create an intensely satisfying tactile visual
  process: precision cutting, clean peeling, perfect stacking, smooth pouring,
  mesmerizing shaping, pressure/texture transformation, glossy materials, or
  immaculate repetitive motion. The action must be physically coherent and the
  payoff must be visually rewarding. Include crisp natural ASMR sound cues.
- Do NOT mix the two pillars in one video. Do NOT create inspirational stories,
  fantasy landscapes, generic cinematic montages, or talking-head content.

TREND SIGNALS:
{trend_lines}

{source_note}

RETENTION AND VISUAL QUALITY:
Create one original concept designed to stop scrolling in the FIRST 0.5-1 second.
The first frame must already show an intriguing action or absurd situation.
Build the clip as 4 connected visual beats within one continuous scene:
1) instant hook,
2) action begins immediately,
3) escalation / close-up payoff,
4) memorable ending that can loop naturally.
Use dynamic but controlled camera movement, macro detail where useful, rich
realistic textures, clean composition, strong lighting, and fluid motion.
Make the main subject large and clear in a 9:16 frame. No empty establishing shot.
Use natural synchronized sound effects / ASMR appropriate to the action.
No narration, no subtitles, no readable text, no logos, no watermarks.
Avoid dangerous stunts, gore, copyrighted characters, and copying any creator's video.

Return ONLY valid JSON with this exact structure:
{{
  "title": "short internal title",
  "format": "Funny AI or Satisfying",
  "trend_basis": "which signal inspired the idea, or say evergreen concept",
  "concept": "one-sentence description",
  "video_prompt": "detailed generation prompt for a 9:16 vertical video, describing the exact subject, action, 4 connected beats, camera, lighting, texture, and synchronized sound",
  "caption": "short catchy TikTok caption",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}

The video_prompt must describe one coherent, high-quality 10-second clip that can
be extended once. Prioritize visual impact and replay value over complexity.
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
                "Continue this exact video seamlessly for up to 10 more seconds. Preserve the selected content pillar and "
                "Preserve the same subject, visual identity, environment, motion logic, "
                "lighting and audio mood. Add a fresh visual development and finish "
                "with a stronger visual punchline for Funny AI or a more rewarding tactile payoff for Satisfying. ""Finish with a memorable loop-friendly ending. Keep it vertical 9:16."
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
    print(f"Daily category: {DAILY_CATEGORY}")

    idea, trends = choose_trend_brief(trends)

    print("\nSelected concept:")
    print(json.dumps(idea, ensure_ascii=False, indent=2))

    generate_video(idea["video_prompt"], OUTPUT_VIDEO)

    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "trend_geo": TREND_GEO,
        "daily_category": DAILY_CATEGORY,
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
