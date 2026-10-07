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
GRANDMA_IMAGE = "grandma.png"
MOM_IMAGE = "mom.png"


# ============================================================
# CHARACTERS
# ============================================================

CHARACTERS = [
    "baby",
    "grandma",
]


# ============================================================
# CREATE STORY
# ============================================================

def generate_story(client):

    print("================================")
    print("Creating a new baby story...")
    print("================================")

    prompt = """
You are the head writer for a viral silent 3D cartoon TikTok channel.

The main character is one adorable toddler.

The toddler NEVER speaks.

There is:
- no dialogue
- no talking
- no lip sync
- no subtitles
- no text on screen

The story must be understood completely through:
facial expressions,
body language,
gestures,
movement,
eye contact,
reactions,
and interaction.

AVAILABLE CHARACTERS:

1. BABY
The main toddler.

2. GRANDMA
A loving grandmother.

The story can use:
- the baby alone
OR
- the baby and grandma together.

Choose ONE of these two options randomly.

IMPORTANT STORY RULE:

Do NOT create four unrelated scenes.

Create ONE SINGLE STORY.

The story must have:

ACT 1:
A clear beginning and situation.

ACT 2:
Something happens that creates a small problem,
desire, surprise, misunderstanding or emotional situation.

ACT 3:
The situation becomes more interesting.

ACT 4:
A satisfying, funny, cute or emotional ending.

Every scene MUST directly cause or continue the next scene.

The viewer should be able to understand:
"What happened?"
"What does the baby want?"
"What is the problem?"
"How does it end?"

The story should feel like a tiny silent movie.

Examples of good story structures:

The grandmother visits the house.
The baby becomes very attached to her.
Grandma gets ready to leave.
The baby becomes sad and stops her.
Grandma decides to stay.
Happy ending.

OR:

The baby finds a box.
He wants to open it.
He tries several funny ways.
He finally opens it and discovers something cute.

OR:

Grandma is eating a snack.
The baby notices it.
He tries to get her attention.
Grandma pretends not to notice.
The baby comes up with a funny solution.
Grandma laughs and shares it.

Use simple everyday situations.

Avoid:
danger,
violence,
weapons,
horror,
injury,
scary situations,
dangerous objects.

Do not add random characters.

Do not suddenly change location without a story reason.

Do not introduce an object and completely forget about it.

The final scene must resolve the main situation.

Return ONLY valid JSON.

Use EXACTLY this structure:

{
  "title": "short title",
  "characters": ["baby", "grandma"],
  "story_goal": "what the baby wants",
  "problem": "the main problem",
  "ending": "how the story ends",
  "scenes": [
    {
      "scene": 1,
      "purpose": "beginning",
      "description": "detailed visual description"
    },
    {
      "scene": 2,
      "purpose": "problem",
      "description": "detailed visual description"
    },
    {
      "scene": 3,
      "purpose": "escalation",
      "description": "detailed visual description"
    },
    {
      "scene": 4,
      "purpose": "ending",
      "description": "detailed visual description"
    }
  ]
}
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

    if "scenes" not in story:

        print("ERROR: Story has no scenes.")
        sys.exit(1)

    if len(story["scenes"]) != 4:

        print("ERROR: Story must contain exactly 4 scenes.")
        sys.exit(1)

    print("================================")
    print("NEW STORY")
    print("================================")

    print("Title:", story.get("title"))

    print(
        "Characters:",
        story.get("characters")
    )

    print(
        "Goal:",
        story.get("story_goal")
    )

    print(
        "Problem:",
        story.get("problem")
    )

    print(
        "Ending:",
        story.get("ending")
    )

    print("================================")

    for scene in story["scenes"]:

        print(
            "Scene",
            scene["scene"],
            ":",
            scene["description"]
        )

    return story


# ============================================================
# CHARACTER IMAGE
# ============================================================

def get_reference_image(characters):

    if "grandma" in characters:

        if not os.path.exists(GRANDMA_IMAGE):

            print("ERROR: grandma.png not found.")

            sys.exit(1)

        return GRANDMA_IMAGE

    if "baby" in characters:

        if not os.path.exists(BABY_IMAGE):

            print("ERROR: baby.png not found.")

            sys.exit(1)

        return BABY_IMAGE

    print("ERROR: No valid character.")

    sys.exit(1)


# ============================================================
# CREATE VEO PROMPT
# ============================================================

def create_video_prompt(
    story,
    scene
):

    characters = story["characters"]

    character_description = """

MAIN BABY CHARACTER:

Use the exact baby shown in the reference image.

Preserve:
- curly brown hair
- large hazel eyes
- same face
- same skin tone
- same age
- same cute 3D cartoon proportions
- same overall appearance

Do NOT redesign the baby.

The baby is SILENT.

The baby does not speak.
The baby does not move lips as if speaking.
No dialogue.
No subtitles.
No text.
"""

    if "grandma" in characters:

        character_description += """

GRANDMOTHER:

The grandmother is a kind older woman.

Preserve her appearance from the reference image.

She has:
- brown hair with natural gray streaks
- hair tied back
- warm friendly face
- pearl earrings
- cream knitted cardigan
- dark floral blouse

Keep her visually consistent.

The grandmother does not speak.

No dialogue.
No subtitles.
No text.
"""

    prompt = f"""
Create an 8-second vertical 3D cartoon animation
for a silent TikTok story.

This is ONE SCENE from a larger continuous story.

STORY TITLE:
{story["title"]}

STORY GOAL:
{story["story_goal"]}

MAIN PROBLEM:
{story["problem"]}

ENDING:
{story["ending"]}

CHARACTERS:
{", ".join(characters)}

{character_description}

PREVIOUS STORY CONTEXT:

The previous scenes establish the following story:

"""

    for previous_scene in story["scenes"]:

        if previous_scene["scene"] < scene["scene"]:

            prompt += (
                f"""
Scene {previous_scene["scene"]}:
{previous_scene["description"]}

"""
            )

    prompt += f"""

CURRENT SCENE:

{scene["description"]}

IMPORTANT:

This scene MUST continue directly from the previous scene.

Keep:
- same characters
- same clothes
- same environment
- same objects
- same time of day
- same visual style

Do not reset the story.

Do not introduce unrelated objects.

Do not introduce new people.

The characters must behave naturally.

Use expressive:
facial expressions,
eye movements,
gestures,
body language,
and toddler reactions.

The baby NEVER speaks.

No talking.
No dialogue.
No lip-sync.
No subtitles.
No text.

Cute family-friendly 3D animated movie style.

Warm cinematic lighting.

Vertical 9:16 composition.

Make the action very clear and easy to understand.
"""

    return prompt


# ============================================================
# GENERATE SCENE
# ============================================================

def generate_scene(
    client,
    story,
    scene
):

    scene_number = scene["scene"]

    output_file = (
        f"scene_{scene_number}.mp4"
    )

    raw_file = (
        f"scene_{scene_number}_raw.mp4"
    )

    print("================================")
    print(
        "Generating scene",
        scene_number
    )
    print("================================")

    reference_path = get_reference_image(
        story["characters"]
    )

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
            "Waiting for Veo scene",
            scene_number,
            "..."
        )

        time.sleep(10)

        operation = client.operations.get(
            operation
        )

    if not operation.response:

        print(
            "ERROR: Veo returned no response."
        )

        sys.exit(1)

    generated_video = (
        operation.response
        .generated_videos[0]
    )

    print(
        "Downloading scene",
        scene_number
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
        "Scene",
        scene_number,
        "created successfully."
    )

    return output_file


# ============================================================
# COMBINE SCENES
# ============================================================

def combine_videos(video_files):

    print("================================")
    print("Combining scenes...")
    print("================================")

    concat_file = "videos.txt"

    with open(
        concat_file,
        "w"
    ) as file:

        for video in video_files:

            absolute_path = os.path.abspath(
                video
            )

            file.write(
                f"file '{absolute_path}'\n"
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

        print(
            "FFmpeg combine error:"
        )

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

        print(
            "ERROR: GEMINI_API_KEY is missing."
        )

        sys.exit(1)

    print(
        "GEMINI_API_KEY found."
    )

    print(
        "Starting silent baby story bot..."
    )

    client = genai.Client(
        api_key=API_KEY
    )

    story = generate_story(
        client
    )

    video_files = []

    for scene in story["scenes"]:

        video = generate_scene(

            client,

            story,

            scene
        )

        video_files.append(
            video
        )

    combine_videos(
        video_files
    )


if __name__ == "__main__":

    main()
