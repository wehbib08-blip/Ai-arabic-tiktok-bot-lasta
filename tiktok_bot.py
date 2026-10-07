import os
import sys
import json
import time
import subprocess

from google import genai
from google.genai import types


# ============================================================
# FILES
# ============================================================

CHARACTER_BIBLE_FILE = "character_bible.json"
MASTER_PROMPT_FILE = "master_prompt.txt"

BABY_IMAGE = "baby.png"
BABY_GRANDMA_IMAGE = "baby_grandma.png"

OUTPUT_VIDEO = "tiktok_story.mp4"


# ============================================================
# API
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY is missing.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)


# ============================================================
# LOAD CHARACTER BIBLE
# ============================================================

def load_character_bible():

    if not os.path.exists(CHARACTER_BIBLE_FILE):
        print(f"ERROR: {CHARACTER_BIBLE_FILE} not found.")
        sys.exit(1)

    try:
        with open(
            CHARACTER_BIBLE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print("ERROR: Could not read character_bible.json")
        print(error)

        sys.exit(1)


# ============================================================
# LOAD MASTER PROMPT
# ============================================================

def load_master_prompt():

    if not os.path.exists(MASTER_PROMPT_FILE):
        print(f"ERROR: {MASTER_PROMPT_FILE} not found.")
        sys.exit(1)

    try:

        with open(
            MASTER_PROMPT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except Exception as error:

        print("ERROR: Could not read master_prompt.txt")
        print(error)

        sys.exit(1)


CHARACTER_BIBLE = load_character_bible()

MASTER_PROMPT = load_master_prompt()

CHARACTER_BIBLE_TEXT = json.dumps(
    CHARACTER_BIBLE,
    ensure_ascii=False,
    indent=2
)


# ============================================================
# GENERATE STORY
# ============================================================

def generate_story():

    print("")
    print("Generating a new story with Gemini...")
    print("")

    prompt = f"""
{MASTER_PROMPT}

==================================================
CHARACTER BIBLE
==================================================

{CHARACTER_BIBLE_TEXT}

==================================================
YOUR TASK
==================================================

Create ONE completely new silent story.

The story must use ONLY:
- baby
- grandma

The story can use:
- baby alone
OR
- baby + grandma

Do NOT use any old Toti characters.

Do NOT invent additional characters.

The story must be one continuous mini movie.

It must contain exactly 4 connected scenes.

Scene 1 = hook and setup.
Scene 2 = problem.
Scene 3 = escalation and attempt.
Scene 4 = resolution and memorable ending.

The story must be understandable without dialogue.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "title": "short story title",

  "characters": [
    "baby"
  ],

  "location": "main location",

  "story_goal": "what the baby wants",

  "problem": "main problem",

  "ending": "how the story ends",

  "scenes": [
    {{
      "scene": 1,
      "purpose": "hook_setup",
      "description": "detailed visual description"
    }},
    {{
      "scene": 2,
      "purpose": "problem",
      "description": "detailed visual description"
    }},
    {{
      "scene": 3,
      "purpose": "escalation",
      "description": "detailed visual description"
    }},
    {{
      "scene": 4,
      "purpose": "resolution",
      "description": "detailed visual description"
    }}
  ]
}}

IMPORTANT:

The four scenes MUST be connected.

Scene 2 must continue directly from Scene 1.

Scene 3 must continue directly from Scene 2.

Scene 4 must continue directly from Scene 3.

Do not create four unrelated ideas.

Do not add dialogue.

Do not add narration.

Do not add subtitles.

Do not add text.

Make the story visually expressive, cute, funny or emotional.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

    except Exception as error:

        print("ERROR: Gemini story generation failed.")
        print(error)

        sys.exit(1)

    try:

        story = json.loads(response.text)

    except Exception as error:

        print("ERROR: Gemini did not return valid JSON.")
        print(response.text)
        print(error)

        sys.exit(1)

    # --------------------------------------------------------
    # Validate story
    # --------------------------------------------------------

    scenes = story.get("scenes", [])

    if len(scenes) != 4:

        print("ERROR: Story must contain exactly 4 scenes.")

        print(json.dumps(
            story,
            ensure_ascii=False,
            indent=2
        ))

        sys.exit(1)

    allowed_characters = {
        character.get("name")
        for character in CHARACTER_BIBLE.get(
            "characters",
            []
        )
    }

    used_characters = set(
        story.get("characters", [])
    )

    if not used_characters.issubset(
        allowed_characters
    ):

        print(
            "ERROR: Gemini invented a character "
            "not present in character_bible.json."
        )

        print("Allowed:")
        print(allowed_characters)

        print("Used:")
        print(used_characters)

        sys.exit(1)

    print("")
    print("========================================")
    print("STORY")
    print("========================================")

    print(
        json.dumps(
            story,
            ensure_ascii=False,
            indent=2
        )
    )

    print("========================================")
    print("")

    return story


# ============================================================
# GET REFERENCE IMAGE
# ============================================================

def get_reference_image(story):

    characters = story.get(
        "characters",
        []
    )

    # Baby + Grandma
    if "grandma" in characters:

        image_path = BABY_GRANDMA_IMAGE

    # Baby only
    else:

        image_path = BABY_IMAGE

    if not os.path.exists(image_path):

        print(
            f"ERROR: Reference image not found: "
            f"{image_path}"
        )

        sys.exit(1)

    return image_path


# ============================================================
# CREATE VEO PROMPT
# ============================================================

def create_video_prompt(
    story,
    scene,
    previous_scene,
    next_scene
):

    characters = story.get(
        "characters",
        []
    )

    character_names = ", ".join(
        characters
    )

    prompt = f"""
Create ONE scene from a continuous silent 3D animated short movie.

This is NOT a standalone video.

The scene must continue naturally from the previous scene
and prepare the next scene.

==================================================
STORY
==================================================

Title:
{story.get("title", "")}

Characters:
{character_names}

Location:
{story.get("location", "")}

Story goal:
{story.get("story_goal", "")}

Main problem:
{story.get("problem", "")}

Ending:
{story.get("ending", "")}

==================================================
CHARACTER BIBLE
==================================================

{CHARACTER_BIBLE_TEXT}

==================================================
PREVIOUS SCENE
==================================================

{previous_scene}

==================================================
CURRENT SCENE
==================================================

{scene.get("description", "")}

==================================================
NEXT SCENE
==================================================

{next_scene}

==================================================
VISUAL RULES
==================================================

Use the provided reference image as the identity reference.

Keep the exact same characters.

Do NOT redesign the characters.

Do NOT change their faces.

Do NOT change their eyes.

Do NOT change their hair.

Do NOT change their clothes.

Do NOT change their age.

Do NOT change their body proportions.

Preserve character identity exactly.

Keep the environment visually consistent.

Keep important objects consistent.

This is a silent visual story.

NO dialogue.

NO speech.

NO lip-sync.

NO subtitles.

NO text on screen.

The characters communicate only through:

facial expressions,
eye contact,
gestures,
body language,
movement,
and reactions.

Style:

cute polished high-quality 3D animated movie.

Warm cinematic lighting.

Natural animation.

Expressive facial reactions.

Vertical 9:16 composition.

The scene must feel like part of ONE continuous movie.
"""

    return prompt


# ============================================================
# GENERATE ONE VEO SCENE
# ============================================================

def generate_scene_video(
    prompt,
    reference_image,
    output_path
):

    print("")
    print("Generating Veo scene...")
    print("")

    try:

        image = types.Image.from_file(
            location=reference_image
        )

        operation = client.models.generate_videos(

            model="veo-3.1-lite-generate-preview",

            prompt=prompt,

            image=image,

            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                resolution="720p",
                number_of_videos=1,
                duration_seconds=8
            )
        )

    except Exception as error:

        print("ERROR: Veo generation failed.")
        print(error)

        sys.exit(1)

    print("Waiting for Veo...")

    while not operation.done:

        time.sleep(10)

        operation = client.operations.get(
            operation
        )

    if operation.error:

        print("ERROR: Veo operation failed.")
        print(operation.error)

        sys.exit(1)

    try:

        video = operation.response.generated_videos[0]

        client.files.download(
            file=video.video,
            download_path=output_path
        )

    except Exception as error:

        print("ERROR: Could not download generated video.")
        print(error)

        sys.exit(1)

    print(
        f"Scene saved: {output_path}"
    )


# ============================================================
# REMOVE AUDIO
# ============================================================

def remove_audio(
    input_file,
    output_file
):

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-an",
        "-c:v",
        "copy",
        output_file
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(
            "ERROR: FFmpeg audio removal failed."
        )

        print(result.stderr)

        sys.exit(1)


# ============================================================
# COMBINE SCENES
# ============================================================

def combine_videos(scene_files):

    print("")
    print("Combining scenes...")
    print("")

    concat_file = "videos.txt"

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as file:

        for scene_file in scene_files:

            file.write(
                f"file '{os.path.abspath(scene_file)}'\n"
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
        "-c",
        "copy",
        OUTPUT_VIDEO
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(
            "ERROR: Could not combine videos."
        )

        print(result.stderr)

        sys.exit(1)

    print("")
    print(
        f"FINAL VIDEO CREATED: {OUTPUT_VIDEO}"
    )
    print("")


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("========================================")
    print("     SILENT BABY STORY BOT")
    print("========================================")
    print("")

    # 1. Gemini creates one connected story
    story = generate_story()

    # 2. Select official reference image
    reference_image = get_reference_image(
        story
    )

    print(
        f"Reference image: {reference_image}"
    )

    scene_files = []

    scenes = story["scenes"]

    # 3. Generate four connected Veo scenes
    for index, scene in enumerate(
        scenes
    ):

        previous_scene = ""

        next_scene = ""

        if index > 0:
            previous_scene = scenes[
                index - 1
            ].get(
                "description",
                ""
            )

        if index < len(scenes) - 1:
            next_scene = scenes[
                index + 1
            ].get(
                "description",
                ""
            )

        prompt = create_video_prompt(
            story,
            scene,
            previous_scene,
            next_scene
        )

        raw_file = (
            f"scene_{index + 1}_raw.mp4"
        )

        clean_file = (
            f"scene_{index + 1}.mp4"
        )

        generate_scene_video(
            prompt,
            reference_image,
            raw_file
        )

        remove_audio(
            raw_file,
            clean_file
        )

        scene_files.append(
            clean_file
        )

    # 4. Combine everything
    combine_videos(
        scene_files
    )

    print("")
    print("========================================")
    print("DONE")
    print("========================================")
    print(
        f"Output: {OUTPUT_VIDEO}"
    )
    print("")


if __name__ == "__main__":
    main()
