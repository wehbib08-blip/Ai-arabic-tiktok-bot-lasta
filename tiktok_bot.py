import os
import sys
import requests
from pathlib import Path
import fal_client


# ============================================================
# SETTINGS
# ============================================================

# FAL model
MODEL = "fal-ai/wan/v2.2-a14b/text-to-video"

# Default video prompt
DEFAULT_PROMPT = """
Create a high-quality vertical TikTok video.
9:16 portrait format.
Fast-paced, visually interesting, realistic cinematic style.
No text on screen.
No logos or watermarks.
The video should look natural and engaging for social media.
"""


# ============================================================
# CHECK API KEY
# ============================================================

def check_fal_key():
    key = os.environ.get("FAL_KEY")

    if not key:
        print("ERROR: FAL_KEY is not configured.")
        print("Add FAL_KEY to GitHub Secrets.")
        sys.exit(1)

    print("FAL_KEY found.")


# ============================================================
# GENERATE VIDEO
# ============================================================

def generate_video(prompt: str, output_file: str = "tiktok_video.mp4"):
    print("\nStarting FAL video generation...")
    print("Prompt:")
    print(prompt)

    try:
        result = fal_client.subscribe(
            MODEL,
            arguments={
                "prompt": prompt,
            },
            with_logs=True,
        )

    except Exception as e:
        print("\nFAL generation failed:")
        print(e)
        sys.exit(1)

    print("\nFAL generation completed.")
    print("Result:")
    print(result)

    # Try to locate the generated video URL
    video_url = None

    if isinstance(result, dict):
        video_data = result.get("video")

        if isinstance(video_data, dict):
            video_url = video_data.get("url")

        if not video_url:
            video_url = result.get("video_url")

    if not video_url:
        print("\nERROR: FAL returned no video URL.")
        print("Full response:")
        print(result)
        sys.exit(1)

    print("\nDownloading video...")
    print(video_url)

    response = requests.get(video_url, timeout=300)
    response.raise_for_status()

    Path(output_file).write_bytes(response.content)

    file_size = Path(output_file).stat().st_size

    print("\n========================================")
    print("VIDEO CREATED SUCCESSFULLY")
    print("File:", output_file)
    print("Size:", file_size, "bytes")
    print("========================================")

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():
    check_fal_key()

    # Allow a custom prompt from GitHub Actions
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = DEFAULT_PROMPT

    generate_video(prompt)


if __name__ == "__main__":
    main()
