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

It must contain exactly 8 connected scenes.

Scene 1 = hook and setup.
Scene 2 = establish the goal.
Scene 3 = problem appears.
Scene 4 = emotional reaction.
Scene 5 = escalation.
Scene 6 = attempt to solve the problem.
Scene 7 = resolution begins.
Scene 8 = memorable emotional or funny ending.

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
    {
      "scene": 1,
      "purpose": "hook_setup",
      "description": "detailed visual description"
    },
    {
      "scene": 2,
      "purpose": "goal",
      "description": "detailed visual description"
    },
    {
      "scene": 3,
      "purpose": "problem",
      "description": "detailed visual description"
    },
    {
      "scene": 4,
      "purpose": "reaction",
      "description": "detailed visual description"
    },
    {
      "scene": 5,
      "purpose": "escalation",
      "description": "detailed visual description"
    },
    {
      "scene": 6,
      "purpose": "attempt",
      "description": "detailed visual description"
    },
    {
      "scene": 7,
      "purpose": "resolution",
      "description": "detailed visual description"
    },
    {
      "scene": 8,
      "purpose": "ending",
      "description": "detailed visual description"
    }
  ]
}}

IMPORTANT:

All eight scenes MUST be connected.

Every scene must continue directly from the previous scene.

Scene 8 must clearly resolve the main problem and end the story.

Do not create four unrelated ideas.

Do not add dialogue.

Do not add narration.

Do not add subtitles.

Do not add text.

Make the story visually expressive, cute, funny or emotional.

Every scene must contain clear physical character actions and interactions.
Describe what each character DOES, not just what the camera sees.
Each scene should have at least 2-4 meaningful actions or reactions.
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

    if len(scenes) != 8:

        print("ERROR: Story must contain exactly 8 scenes.")

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
Create ONE NEWLY GENERATED 3D ANIMATED SCENE from a continuous animated short movie.

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

USE THE PROVIDED IMAGE ONLY AS A CHARACTER IDENTITY REFERENCE.

The reference image is NOT the scene to animate.

DO NOT simply animate, pan, zoom, crop, or move the source image.

DO NOT make the result look like a photograph being moved.

RECREATE the characters as fully animated 3D characters inside a newly generated
3D environment that fits the current story scene.

The characters must perform real physical actions appropriate to the scene:
walking, standing, sitting, reaching, picking up objects, turning, hugging,
running, playing, reacting, crying, laughing, or interacting with each other.

Keep the exact same character identities.

Do NOT redesign the characters.

Do NOT change their faces.

Do NOT change their eyes.

Do NOT change their hair.

Do NOT change their clothes.

Do NOT change their age.

Do NOT change their body proportions.

Preserve character identity exactly.

The environment should be newly generated for the story, while remaining
consistent from scene to scene.

Keep important story objects consistent.

This is a visual-first animated story with natural sound.

Do NOT create long dialogue or conversations.

Short natural words are allowed when they improve the story, especially for the baby,
for example: "mama", "teta", "no", "bye", "this", or a short happy/excited sound.

No long speeches.

No narration.

No subtitles.

No text on screen.

The baby can make natural toddler sounds, giggles, cries, surprised sounds,
and very short words.

Grandma may use at most very short natural words when needed.

Include pleasant synchronized audio:
- gentle cheerful background music appropriate for a cute family animation
- natural room/environment sounds
- footsteps and movement sounds when appropriate
- soft object interaction sounds
- baby giggles, gasps, or cries when appropriate
- warm emotional musical ending

Audio must support the story without overpowering the characters.

ACTION DIRECTION:

Prioritize character animation over camera movement.

The main subject must visibly move through the scene.

Show full-body or medium shots when needed so the viewer can clearly see the
character walking, reaching, carrying, sitting, standing, hugging, reacting,
or interacting with objects.

Use close-ups only for important emotional reactions.

Avoid long shots where the character barely moves.

Style:

cute polished high-quality 3D animated movie.

Warm cinematic lighting.

Natural animation.

Expressive facial reactions.

Vertical 9:16 composition.

The scene must feel like part of ONE continuous movie.

The reference image must NOT remain visible as a static image.
Generate the characters anew and animate them performing the described actions.

Generate synchronized native audio for the scene.
Use gentle background music and appropriate sound effects.
Do not make the audio silent.

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

            source=types.GenerateVideosSource(
                prompt=prompt,
                image=image
            ),

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
            destination=output_path
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
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
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

    # 3. Generate eight connected Veo scenes with native audio
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

        # Keep Veo's native audio: music, ambience, sound effects,
        # and short natural character sounds.
        scene_files.append(
            raw_file
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
