import os
import sys
import time

from google import genai
from google.genai import types


API_KEY = os.environ.get("GEMINI_API_KEY")
OUTPUT_FILE = "tiktok_story.mp4"


PROMPT = """
Vertical 9:16 animated family scene for TikTok.

A warm Lebanese family in a cozy modern family living room.

There are exactly three characters:

1. Toti:
A cute 10-year-old Arabic girl.
Chestnut-brown wavy hair, large hazel eyes, fair skin,
sweet cheerful personality.

She wears a cream floral sweater,
loose light-blue cargo jeans,
and white and pink sneakers.

She is the family's young daughter.

2. Reem:
Toti's mother, a young adult Lebanese woman.
Brown hair, warm friendly face,
elegant casual home clothes.

Keep her appearance consistent with the provided reference image.

3. Abdullah:
Toti's father, a young adult Lebanese man.
Dark wavy hair, short beard, warm friendly face,
casual family clothes.

Keep his appearance consistent with the provided reference image.

SCENE:

The three family members are together in the living room.

Toti walks toward her mother and father excitedly.
She smiles and says naturally in Arabic:

"ماما، بابا، بدي خبركن شو صار معي اليوم!"

Her mother looks at her with a warm smile.

Her father smiles and listens.

Warm family atmosphere.
Cozy Lebanese home.
High-quality 3D animated children's film style.
Natural character movement.
Expressive faces.
Cinematic camera movement.

No subtitles.
No text on screen.
No extra people.
Exactly three characters.
Keep the characters consistent throughout the entire video.
"""


def generate_video():

    if not API_KEY:
        print("ERROR: GEMINI_API_KEY is missing.")
        sys.exit(1)

    print("GEMINI_API_KEY found.")
    print("Starting Veo 3.1 family test...")

    client = genai.Client(api_key=API_KEY)

    # Load the two adult reference images
    print("Loading mom.png...")
    mom_image = types.Image.from_file(location="mom.png")

    print("Loading dad.png...")
    dad_image = types.Image.from_file(location="dad.png")

    # Create reference images
    mom_reference = types.VideoGenerationReferenceImage(
        image=mom_image,
        reference_type="asset",
    )

    dad_reference = types.VideoGenerationReferenceImage(
        image=dad_image,
        reference_type="asset",
    )

    print("Starting video generation...")

    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=PROMPT,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="720p",
            number_of_videos=1,
            person_generation="allow_adult",
            duration_seconds="8",
            reference_images=[
                mom_reference,
                dad_reference,
            ],
        ),
    )

    # Wait for Veo to finish
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
    print("FAMILY TEST VIDEO CREATED")
    print("File:", OUTPUT_FILE)
    print("================================")


if __name__ == "__main__":
    generate_video()
