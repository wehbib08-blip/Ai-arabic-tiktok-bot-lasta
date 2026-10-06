import os
import sys
import time
import subprocess

from google import genai
from google.genai import types


API_KEY = os.environ.get("GEMINI_API_KEY")

OUTPUT_FILE = "tiktok_story.mp4"


# =========================
# CHARACTER SCENES
# =========================

SCENES = [
    {
        "name": "toti",
        "image": "toti.png",
        "prompt": """
Animate this character into an 8-second vertical TikTok scene.

This is Toti, a 10-year-old Arabic girl.

Keep her face, hair, eyes, clothes, age and overall appearance
consistent with the input image.

Scene:
Toti is sitting in a cozy Lebanese family living room.

She looks happy and excited.
She moves naturally and looks toward the camera.

She says naturally in Arabic:

"ماما، بابا، بدي خبركن شو صار معي اليوم!"

Natural facial expressions.
Natural blinking and breathing.
Small realistic body movements.
Warm family atmosphere.
High-quality 3D animated movie style.

Do not change her appearance.
Do not add other people.
No subtitles.
No text on screen.
"""
    },

    {
        "name": "mom",
        "image": "mom.png",
        "prompt": """
Animate this character into an 8-second vertical TikTok scene.

This is Reem, Toti's mother.

Keep her face, hair, eyes, clothes and overall appearance
consistent with the input image.

Scene:
Reem is sitting in the same cozy Lebanese family living room.

She smiles warmly and listens to Toti.

She naturally says in Arabic:

"خير يا ماما؟ خبريني شو صار."

Natural facial expressions.
Natural blinking and breathing.
Small realistic body movements.
Warm Lebanese family atmosphere.
High-quality 3D animated movie style.

Do not change her appearance.
Do not add other people.
No subtitles.
No text on screen.
"""
    },

    {
        "name": "dad",
        "image": "dad.png",
        "prompt": """
Animate this character into an 8-second vertical TikTok scene.

This is Abdullah, Toti's father.

Keep his face, hair, beard, clothes and overall appearance
consistent with the input image.

Scene:
Abdullah is sitting in the same cozy Lebanese family living room.

He smiles warmly and listens to Toti.

He naturally says in Arabic:

"يلا توتي، خبرينا شو صار."

Natural facial expressions.
Natural blinking and breathing.
Small realistic body movements.
Warm Lebanese family atmosphere.
High-quality 3D animated movie style.

Do not change his appearance.
Do not add other people.
No subtitles.
No text on screen.
"""
    }
]


# =========================
# GENERATE ONE VIDEO
# =========================

def generate_character_video(client, scene):

    name = scene["name"]
    image_path = scene["image"]

    output_file = f"{name}.mp4"

    print("================================")
    print(f"Generating {name}...")
    print("Image:", image_path)
    print("================================")

    if not os.path.exists(image_path):
        print(f"ERROR: {image_path} not found.")
        sys.exit(1)

    character_image = types.Image.from_file(
        location=image_path
    )

    operation = client.models.generate_videos(
        model="veo-3.1-lite-generate-preview",
        prompt=scene["prompt"],
        image=character_image,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="720p",
            number_of_videos=1,
            duration_seconds=8,
        ),
    )

    while not operation.done:
        print(f"Waiting for {name}...")
        time.sleep(10)
        operation = client.operations.get(operation)

    if not operation.response:
        print(f"ERROR: Veo returned no response for {name}.")
        sys.exit(1)

    generated_video = operation.response.generated_videos[0]

    print(f"Downloading {name}...")

    client.files.download(
        file=generated_video.video,
        destination=output_file,
    )

    print(f"{name} video created.")

    return output_file


# =========================
# JOIN VIDEOS
# =========================

def combine_videos(video_files):

    print("================================")
    print("Combining character videos...")
    print("================================")

    concat_file = "videos.txt"

    with open(concat_file, "w") as f:
        for video in video_files:
            absolute_path = os.path.abspath(video)
            f.write(f"file '{absolute_path}'\n")

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
        "-pix_fmt",
        "yuv420p",
        OUTPUT_FILE
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

   if result.returncode != 0:
