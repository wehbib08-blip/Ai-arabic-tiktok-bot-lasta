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


# ==================================================
# GEMINI CREATES A NEW STORY
# ==================================================

def generate_story(client):

    print("================================")
    print("Creating a new baby story...")
    print("================================")

    prompt = """
You are a creative director for short viral TikTok videos.

Create ONE new cute, funny and visually understandable story
about an adorable toddler.

The story is completely SILENT.

The baby never speaks.
The baby never talks.
There is no dialogue.
There is no lip-sync.
There are no subtitles.
There is no text on screen.

The story must be understood through:

facial expressions,
eye movements,
hand gestures,
pointing,
crawling,
walking,
playing,
reactions,
and interaction with objects.

Create exactly 4 connected scenes.

Each scene must continue naturally from the previous scene.

The story must be:
cute,
funny,
family-friendly,
easy to understand,
and visually interesting.

Use simple everyday objects such as:
toys,
balls,
stuffed animals,
boxes,
balloons,
food,
books,
or household objects.

Do not use:
dangerous situations,
weapons,
violence,
frightening scenes,
or other people.

Return ONLY valid JSON.

Use exactly this structure:

{
  "title": "short story title",
  "scenes": [
    {
      "scene": 1,
      "description": "description of scene 1"
    },
    {
      "scene": 2,
      "description": "description of scene 2"
    },
    {
      "scene": 3,
      "description": "description of scene 3"
    },
    {
      "scene": 4,
      "description": "description of scene 4"
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
        print("ERROR: Story does not contain scenes.")
        sys.exit(1)

    if len(story["scenes"]) != 4:
        print("ERROR: Story does not contain exactly 4 scenes.")
        sys.exit(1)

    print("================================")
    print("NEW STORY CREATED")
    print("Title:", story.get("title", "Untitled"))
    print("================================")

    for scene in story["scenes"]:
        print(
            "Scene",
            scene["scene"],
            ":",
            scene["description"]
        )

    return story


# ==================================================
# CREATE VEO PROMPT
# ==================================================

def create_video_prompt(description):

    prompt = f"""
Create an 8-second vertical 3D cartoon animation.

Use the provided baby image as the main character reference.

CHARACTER CONSISTENCY:

Keep exactly the same baby character as the reference image.

Preserve:
- curly brown hair
- large hazel eyes
- same face
- same skin tone
- same age
- same cute cartoon proportions
- same overall appearance

Do not redesign the baby.

SCENE:

{description}

ANIMATION:

Animate the baby naturally and expressively.

Use:
- facial expressions
- eye movements
- hand gestures
- pointing
- body movement
- cute reactions
- natural toddler movement

IMPORTANT:

The baby NEVER speaks.

No talking.
No dialogue.
No lip-sync.
No subtitles.
No text on screen.

Do not add other people.

Keep the scene cute, funny and family-friendly.

High-quality stylized 3D cartoon animation.
Warm cinematic lighting.
Detailed cozy environment.
Vertical 9:16 TikTok composition.
"""

    return prompt


# ==================================================
# GENERATE ONE SCENE WITH VEO
# ==================================================

def generate_scene(client, scene_number, description):

    output_file = f"scene_{scene_number}.mp4"
    raw_file = f"scene_{scene_number}_raw.mp4"

    print("================================")
    print("Generating scene", scene_number)
    print("================================")

    if not os.path.exists(BABY_IMAGE):
        print("ERROR: baby.png not found.")
        sys.exit(1)

    baby_image = types.Image.from_file(
        location=BABY_IMAGE
    )

    video_prompt = create_video_prompt(
        description
    )

    operation = client.models.generate_videos(
        model="veo-3.1-lite-generate-preview",
        prompt=video_prompt,
        image=baby_image,
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
            "ERROR: Veo returned no response for scene",
            scene_number
        )

        sys.exit(1)

    generated_video = (
        operation.response.generated_videos[0]
    )

    print(
        "Downloading scene",
        scene_number,
        "..."
    )

    client.files.download(
        file=generated_video.video,
        destination=raw_file
    )

    # Remove audio because the project is silent.

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


# ==================================================
# COMBINE ALL SCENES
# ==================================================

def combine_videos(video_files):

    print("================================")
    print("Combining all scenes...")
    print("================================")

    concat_file = "videos.txt"

    with open(concat_file, "w") as file:

        for video in video_files:

            absolute_path = os.path.abspath(
                video
            )

            file.write(
                "file '" +
                absolute_path +
                "'\n"
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


# ==================================================
# MAIN
# ==================================================

def main():

    if not API_KEY:

        print(
            "ERROR: GEMINI_API_KEY is missing."
        )

        sys.exit(1)

    print("GEMINI_API_KEY found.")

    print(
        "Starting automatic silent baby TikTok bot..."
    )

    client = genai.Client(
        api_key=API_KEY
    )

    # Gemini creates a completely new story.

    story = generate_story(client)

    video_files = []

    # Veo creates the four scenes.

    for scene in story["scenes"]:

        video = generate_scene(
            client,
            scene["scene"],
            scene["description"]
        )

        video_files.append(video)

    # FFmpeg combines all scenes.

    combine_videos(video_files)


if __name__ == "__main__":
    main()
