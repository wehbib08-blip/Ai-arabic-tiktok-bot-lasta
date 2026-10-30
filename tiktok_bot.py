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

# Rotate three short-form formats daily; same UTC date = same format on reruns.
TODAY_UTC = datetime.now(timezone.utc).date()
FORMAT_ROTATION = ["FUNNY_AI_STORY", "SLOW_MOTION_ZOOM", "SATISFYING_CINEMATIC"]
DAILY_CATEGORY = FORMAT_ROTATION[TODAY_UTC.toordinal() % len(FORMAT_ROTATION)]

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
The channel publishes ONE original vertical video per day.
Today's required format is exactly: {DAILY_CATEGORY}. Do not blend formats.

FORMAT A — FUNNY_AI_STORY:
Create a genuinely funny mini-story with one main character, one simple goal,
one escalating complication, and one clear visual punchline. Use expressive
reactions and excellent comic timing. Make the joke understandable without sound.

FORMAT B — SLOW_MOTION_ZOOM:
Create a visually striking single event built around an extreme macro close-up,
a deliberate smooth push-in or pull-back, a dramatic slow-motion moment, crisp
synchronized sound design, and a strong visual reveal. Examples: a harmless
fictional object bursting into colorful powder, a fruit splitting open in a
surreal clean studio, a droplet hitting liquid, or a beautiful material reveal.
No real injuries or dangerous events. Zoom must be smooth, never jittery.

FORMAT C — SATISFYING_CINEMATIC:
Create a highly satisfying tactile process such as precise cutting of safe soft
materials, smooth pouring, perfect stacking, peeling, shaping, glossy liquid
movement, or clean texture transformations. Use macro details, controlled
camera movement, crisp ASMR sound and a rewarding final result.

TREND SIGNALS:
{trend_lines}

{source_note}

MOTION, CONTINUITY AND EDITING RULES:
- First frame must contain the hook; no slow establishing shot.
- Describe actions chronologically, second by second, for a coherent 10-second clip.
- Use one continuous scene or at most two connected shots.
- Keep subject identity, proportions, texture, colors, props and setting consistent.
- Object interactions must obey simple, believable physical motion.
- No teleporting, morphing, random scene changes, warped anatomy, or camera jitter.
- Choose one clear camera plan: locked macro, smooth dolly-in, smooth dolly-out,
  or one controlled tracking move. Never combine conflicting camera moves.
- For slow motion, specify exactly which brief moment is slowed; surrounding action
  remains at natural speed.
- Add synchronized sound effects: comic accents for comedy, crisp texture sounds
  for satisfying, and cinematic whoosh/impact accents for dramatic reveals.
- Vertical 9:16, premium lighting, detailed textures, clean composition.
- No subtitles, readable text, logos, watermarks, copyrighted characters, gore,
  dangerous stunts, or copying any creator's exact video.

Return ONLY valid JSON with this exact structure:
{{
  "title": "short internal title",
  "format": "{DAILY_CATEGORY}",
  "trend_basis": "trend inspiration or evergreen concept",
  "concept": "one-sentence description",
  "video_prompt": "detailed 10-second vertical video prompt with exact subject, chronological action by seconds, camera move, motion continuity, lighting, and synchronized sound design",
  "caption": "short catchy TikTok caption",
  "hashtags": ["#AIVideo", "#FunnyAI", "#Satisfying", "#SlowMotion", "#TikTok"]
}}

Make the concept instantly understandable and visually memorable. Keep characters
and moving objects few so the video model can maintain coherent motion.
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
                f"Continue this exact {DAILY_CATEGORY} video seamlessly for up to 10 more seconds. "
                "Preserve subject identity, proportions, colors, props, setting, lighting "
                "and visual style. Continue the same action logically; do not introduce "
                "unrelated subjects or change scenes. Keep movement smooth and physically "
                "coherent. For comedy, strengthen the punchline; for slow-motion zoom, "
                "complete the controlled camera reveal; for satisfying, deliver a rewarding "
                "tactile payoff. Finish with a memorable loop-friendly ending. Vertical 9:16."
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
    print("Daily category: FUNNY AI STORY")

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
