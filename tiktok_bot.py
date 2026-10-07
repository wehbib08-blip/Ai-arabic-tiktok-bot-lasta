import os
import sys
import time
import json
import subprocess

from google import genai
from google.genai import types


API_KEY = os.environ.get("GEMINI_API_KEY")

OUTPUT_FILE = "tiktok_story.mp4"
BABY_IMAGE = "baby.png"


# ==========================================
# 1. GEMINI CREATES A NEW SILENT STORY
# ==========================================

def generate_story(client):

    print("================================")
    print("Creating a new baby story...")
    print("================================")

    prompt = """
You are a creative director for short viral TikTok videos.

Create ONE completely new, cute, funny and visually understandable
story starring the same adorable toddler shown in the reference image.

The story must be SILENT.

The baby never talks.
The baby never says words.
There is no dialogue.
There is no lip-sync.

The story must be understandable only through:
- facial expressions
- eye movements
- pointing
- hand gestures
- crawling
- walking
- playing
- reactions
- interaction with objects

Create exactly 4 connected scenes.

Each scene should be visually interesting and continue naturally
from the previous scene.

The story should be suitable for children and families.

Use simple everyday objects such as toys, food, balloons,
stuffed animals, boxes, balls or household objects.

Do not use dangerous situations.
Do not use weapons.
Do not use frightening scenes.
Do not add other people.

Return ONLY valid JSON in this exact structure:

{
  "title": "short story title",
  "scenes": [
    {
      "scene": 1,
      "description": "visual description of scene 1"
    },
    {
      "scene": 2,
      "description": "visual description of scene 2"
    },
    {
      "scene": 3,
      "description": "visual description of scene 3"
    },
    {
      "scene": 4,
      "description": "visual description of scene 4"
    }
  ]
}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    if not response.text:
        print("ERROR: Gemini returned no story.")
        sys.exit(1)

    try:
        story = json.loads(response.text)
    except json.JSONDecodeError:
        print("ERROR: Gemini
