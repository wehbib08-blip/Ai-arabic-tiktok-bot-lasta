import os
import sys
import time
import json
import subprocess
import random

from google import genai
from google.genai import types


API_KEY = os.environ.get("GEMINI_API_KEY")

OUTPUT_FILE = "tiktok_story.mp4"

BABY_IMAGE = "baby.png"
BABY_GRANDMA_IMAGE = "baby_grandma.png"


# ============================================================
# OFFICIAL CHARACTER BIBLE
# ============================================================

CHARACTER_BIBLE = """
OFFICIAL CHARACTER BIBLE — DO NOT CHANGE THESE CHARACTERS.

BABY:
- adorable toddler boy
- cute round face
- warm light skin
- large warm brown/hazel eyes
- very curly dark-brown hair with dense natural curls
- rosy cheeks
- cute toddler proportions
- joyful and highly expressive face
- same age, face, eyes, hair and body proportions in every scene

BABY OFFICIAL OUTFIT:
- cream/beige sweatshirt
- small teddy-bear patch on the chest
- brown/gray pants
- EXACT SAME outfit in every scene

GRANDMA:
- kind loving older woman
- warm light/olive skin
- soft natural facial lines
- warm brown eyes
- brown hair with natural gray streaks
- elegant tied-up hairstyle
- pearl earrings
- gentle warm smile
- same face, hair and body proportions in every scene

GRANDMA OFFICIAL OUTFIT:
- cream knitted cardigan
- dark floral blouse underneath
- pearl earrings
- EXACT SAME outfit in every scene

CHARACTER LOCK:
The characters are permanent recurring characters.

NEVER change:
- facial features
- face shape
- eyes
- eye color
- nose
- mouth
- skin tone
- hair color
- hairstyle
- curl pattern
- age
- body proportions
- height relationship
- clothing
- clothing colors
- clothing patterns
- accessories
- jewelry

Never redesign, reinterpret, replace, beautify differently,
age, or de-age the characters.

The characters must look like the SAME PEOPLE from beginning
to end.

Continuity is more important than visual variation.
"""


# ============================================================
# GEMINI CREATES ONE CONNECTED SILENT SHORT FILM
# ============================================================

def generate_story(client):

    print("================================")
    print("Creating a new connected story...")
    print("================================")

    prompt = f"""
You are the head writer for a viral silent 3D cartoon TikTok channel.

{CHARACTER_BIBLE}

Create ONE complete short silent movie starring:
- the baby alone
OR
- the baby and grandma together.

Choose naturally between these two options.

IMPORTANT:
This is NOT four separate ideas.

It is ONE SINGLE STORY divided into exactly 4 connected scenes.

The story must have:

SCENE 1:
A clear beginning and a simple goal.

SCENE 2:
Something happens that creates a problem, obstacle,
surprise or emotional conflict.

SCENE 3:
The problem becomes more interesting and the baby reacts
or tries to solve it.

SCENE 4:
A satisfying cute, funny or emotional resolution.

Every scene must directly continue from the previous scene.

The viewer must understand:
- what the baby wants
- what happened
- what the problem is
- why the baby reacts
- how the situation ends

Use simple everyday situations.

Examples:
grandma visits and the baby does not want her to leave;
the baby wants something grandma has;
grandma tries to leave and the baby finds a funny way
to convince her to stay;
the baby and grandma play a simple game that becomes funny.

The story must be visual only.

No dialogue.
No speech.
No lip-sync.
No subtitles.
No text on screen.

The baby must NEVER speak.

Grandma must also NEVER speak.

Use facial expressions, eye contact, gestures,
body language, movement and reactions.

No dangerous situations.
No violence.
No weapons.
No horror.
No injury.
No frightening situations.
No extra characters.

Do not randomly change location.
Do not randomly change clothes.
Do not introduce objects that are forgotten later.

Return ONLY valid JSON:

{{
  "title": "short title",
  "characters": ["baby", "grandma"],
  "location": "main location",
  "story_goal": "what the baby wants",
  "problem": "main problem",
  "ending": "how the story resolves",
  "scenes": [
    {{
      "scene": 1,
      "purpose": "beginning",
      "description": "detailed visual action"
    }},
    {{
      "scene": 2,
      "purpose": "problem",
      "description": "detailed visual action"
    }},
    {{
      "scene": 3,
      "purpose": "escalation",
      "description": "detailed visual action"
    }},
    {{
      "scene": 4,
      "purpose": "resolution",
      "description": "detailed visual action"
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
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
        print("ERROR: Gemini returned invalid JSON.")
        print(response.text)
        sys.exit(1)

    if len(story.get("scenes", [])) != 4:
        print("ERROR: Story must contain exactly 4 scenes.")
        print(story)
        sys.exit(1)

    print("================================")
    print("NEW STORY")
    print("Title:", story.get("title"))
    print("Characters:", story.get("characters"))
    print("Goal:", story.get("story_goal"))
    print("Problem:", story.get("problem"))
    print("Ending:", story.get("ending"))
    print("================================")

    for scene in story["scenes"]:
        print(
            f"Scene {scene['scene']}: "
            f"{scene['description']}"
        )

    return story


# ============================================================
# CHOOSE THE CORRECT OFFICIAL REFERENCE
# ============================================================

def get_reference_image(story):

    characters = story.get("characters", [])

    if "grandma" in characters:

        if not os.path.exists(BABY_GRANDMA_IMAGE):
            print("ERROR: baby_grandma.png not found.")
            sys.exit(1)

        return BABY_GRANDMA_IMAGE

    if not os.path.exists(BABY_IMAGE):
        print("ERROR: baby.png not found.")
        sys.exit(1)

    return BABY_IMAGE


# ============================================================
# VEO MASTER PROMPT
# ============================================================

def create_video_prompt(story, current_scene):

    scenes = story["scenes"]
    number = current_scene["scene"]

    previous_context = ""

    for scene in scenes:
        if scene["scene"] < number:
            previous_context += (
                f"\nScene {scene['scene']}:\n"
                f"{scene['description']}\n"
            )

    next_context = ""

    for scene in scenes:
        if scene["scene"] > number:
            next_context = scene["description"]
            break

    prompt = f"""
Create an 8-second vertical 3D cartoon animation.

This is SCENE {number} of ONE continuous silent short movie.

==================================================
OFFICIAL CHARACTER BIBLE
==================================================

{CHARACTER_BIBLE}

==================================================
STORY
==================================================

Title:
{story.get("title")}

Location:
{story.get("location")}

Story goal:
{story.get("story_goal")}

Main problem:
{story.get("problem")}

Ending:
{story.get("ending")}

==================================================
PREVIOUS STORY EVENTS
==================================================

{previous_context}

==================================================
CURRENT SCENE
==================================================

{current_scene["description"]}

==================================================
NEXT STORY BEAT
==================================================

{next_context}

==================================================
ABSOLUTE CONTINUITY RULES
==================================================

Use the provided reference image as the identity reference.

The characters MUST remain exactly the same.

DO NOT change:
- face
- facial proportions
- eyes
- eye color
- hair
- curls
- skin
- age
- body shape
- height relationship
- clothes
- clothing colors
- clothing patterns
- earrings
- accessories

The baby MUST wear the exact same outfit.

Grandma MUST wear the exact same outfit.

Do not add or remove clothing.

Do not change hairstyles.

Do not change character designs.

Do not introduce new people.

Keep the same location and visual environment unless the
story explicitly requires a logical location change.

Keep important objects consistent.

This is a continuation, NOT a new story.

Do not restart the action.

==================================================
SILENT PERFORMANCE
==================================================

No speech.
No talking.
No dialogue.
No lip-sync.
No subtitles.
No text on screen.

The baby never speaks.

Grandma never speaks.

Tell the story only through:
- facial expressions
- eye movements
- gestures
- body language
- movement
- reactions
- interaction with objects

Make the action clear, cute and emotionally readable.

High-quality polished 3D animated movie style.

Warm cinematic lighting.

Vertical 9:16 TikTok composition.

The final frame should naturally lead into the next scene
when there is one.
"""

    return prompt


# ============================================================
# GENERATE ONE SCENE
# ============================================================

def generate_scene(client, story, scene):

    scene_number = scene["scene"]

    raw_file = f"scene_{scene_number}_raw.mp4"
    output_file = f"scene_{scene_number}.mp4"

    print("================================")
    print(f"Generating scene {scene_number}")
    print("================================")

    reference_path = get_reference_image(story)

    reference_image = types.Image.from_file(
        location=reference_path
    )

    prompt = create_video_prompt(
        story,
        scene
    )

    operation = client.models.generate_videos(
        model="veo-3.1-lite-generate-preview",
        prompt=prompt,
        image=reference_image,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="720p",
            number_of_videos=1,
            duration_seconds=8,
        ),
    )

    while not operation.done:

        print(
            f"Waiting for Veo scene {scene_number}..."
        )

        time.sleep(10)

        operation = client.operations.get(operation)

    if not operation.response:

        print(
            f"ERROR: Veo returned no response for scene {scene_number}."
        )

        sys.exit(1)

    generated_video = (
        operation.response.generated_videos[0]
    )

    client.files.download(
        file=generated_video.video,
        destination=raw_file
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        raw_file,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        output_file
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print("FFmpeg error:")
        print(result.stderr)

        sys.exit(1)

    print(
        f"Scene {scene_number} created successfully."
    )

    return output_file


# ============================================================
# COMBINE
# ============================================================

def combine_videos(video_files):

    print("================================")
    print("Combining scenes...")
    print("================================")

    concat_file = "videos.txt"

    with open(concat_file, "w") as file:

        for video in video_files:

            file.write(
                f"file '{os.path.abspath(video)}'\n"
            )

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        OUTPUT_FILE
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print("FFmpeg combine error:")
        print(result.stderr)

        sys.exit(1)

    print("================================")
    print("FINAL VIDEO CREATED")
    print("File:", OUTPUT_FILE)
    print("================================")


# ============================================================
# MAIN
# ============================================================

def main():

    if not API_KEY:

        print("ERROR: GEMINI_API_KEY is missing.")
        sys.exit(1)

    print("GEMINI_API_KEY found.")
    print("Starting connected silent story bot...")

    client = genai.Client(
        api_key=API_KEY
    )

    story = generate_story(client)

    video_files = []

    for scene in story["scenes"]:

        video = generate_scene(
            client,
            story,
            scene
        )

        video_files.append(video)

    combine_videos(video_files)


if __name__ == "__main__":
    main()
