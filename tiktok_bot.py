import os
import sys
import time

from google import genai
from google.genai import types


API_KEY = os.environ.get("GEMINI_API_KEY")
OUTPUT_FILE = "tiktok_story.mp4"


PROMPT = """
Animate this family image into a warm 8-second vertical TikTok scene.

The image contains exactly three family members:
a mother, a father, and their daughter Toti.

Keep all three characters visually consistent with the input image.
Do not change their faces, hair, clothing, age, or overall appearance.

Scene:
The family is sitting together in their cozy living room.

Toti looks happy and excited.
She turns slightly toward her mother and father and naturally says in Arabic:

"ماما، بابا، بدي خبركن شو صار معي اليوم!"

The mother smiles warmly at Toti.
The father smiles and listens.

Natural facial expressions.
Natural small body movements.
Subtle realistic breathing and blinking.
Gentle cinematic camera movement.
Warm Lebanese family atmosphere.
High-quality 3D animated movie style.

Keep exactly the same three people.
Do not add any other people.
No subtitles.
No text on screen.
Do not change the characters' appearance.
"""


def generate_video():

    if not API_KEY:
        print("ERROR: GEMINI_API_KEY is missing.")
        sys.exit(1)

    print("GEMINI_API_KEY found.")
    print("Starting Veo 3.1 Lite image-to-video...")

    client = genai.Client(api_key=API_KEY)

    print("Loading family.png...")

    family_image = types.Image.from_file(
        location="family.png"
    )

    print("Starting video generation...")

    operation = client.models.generate_videos(
        model="veo-3.1-lite-generate-preview",
        source=types.GenerateVideosSource(
            prompt=PROMPT,
            image=family_image,
        ),
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="720p",
            number_of_videos=1,
            duration_seconds=8,
        ),
    )

    while not operation.done:
        print("Waiting for Veo...")
        time.sleep(10)
        operation = client.operations.get(operation)

    if not operation.response:
        print("ERROR: Veo returned no response.")
        sys.exit(1)

    generated_video = operation.response.generated_videos[0]

    print("Downloading video...")

    client.files.download(
        file=generated_video.video,
        destination=OUTPUT_FILE,
    )

    print("================================")
    print("FAMILY VIDEO CREATED")
    print("File:", OUTPUT_FILE)
    print("================================")


if __name__ == "__main__":
    generate_video()
