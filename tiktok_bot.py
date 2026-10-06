import os
import sys
import time
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")

OUTPUT_FILE = "tiktok_story.mp4"

PROMPT = """
Vertical 9:16 animated story scene for TikTok.

A cute 10-year-old Arabic girl named Tala, nicknamed Toti.
She has chestnut-brown hair, large hazel eyes, fair skin, and a cheerful,
sweet personality.

Toti is standing in a cozy family living room in Lebanon.
She looks curious and happy, then walks toward her mother and smiles.

Warm family atmosphere, high-quality 3D animated children's film style,
natural character movement, cinematic camera movement,
detailed environment, expressive face.

Arabic dialogue:
Toti says: "ماما، بدي خبرك شو صار معي اليوم!"

The girl speaks naturally in Arabic.
No subtitles, no text on screen.
Keep the same character appearance throughout the shot.
"""


def generate_video():
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY is missing.")
        sys.exit(1)

    print("GEMINI_API_KEY found.")
    print("Starting Veo 3.1 video generation...")

    client = genai.Client(api_key=API_KEY)

    operation = client.models.generate_videos(
    model="veo-3.1-lite-generate-preview",
    prompt=PROMPT,
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",
        resolution="720p",
        number_of_videos=1,
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

    client.files.download(
        file=generated_video.video,
        destination=OUTPUT_FILE,
    )

    print("================================")
    print("VEO VIDEO CREATED")
    print("File:", OUTPUT_FILE)
    print("================================")


if __name__ == "__main__":
    generate_video()
