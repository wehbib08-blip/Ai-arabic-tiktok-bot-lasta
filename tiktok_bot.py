import os
import sys
import time
import subprocess

from google import genai
from google.genai import types


API_KEY = os.environ.get("GEMINI_API_KEY")
OUTPUT_FILE = "tiktok_story.mp4"


SCENES = [
    {
        "name": "scene1",
        "prompt": """
Create an 8-second vertical silent 3D cartoon scene using the provided baby image.

IMPORTANT:
Keep the exact same baby character throughout the video.
Preserve the baby's face, large hazel eyes, curly brown hair,
skin tone, age, body proportions and clothing.

Scene:
The cute baby is sitting on a cozy playroom floor.
A colorful toy car is a few steps away.

The baby suddenly notices the toy.
He looks at it with curiosity.
His eyes become excited and he points toward the toy.

Use clear baby gestures and expressive facial expressions.

The baby does NOT speak.
No dialogue.
No lip-sync.
No subtitles.
No text.
No other people.

Cute exaggerated 3D cartoon animation.
Natural baby movement.
Warm cinematic lighting.
Vertical 9:16 composition.
"""
    },

    {
        "name": "scene2",
        "prompt": """
Create an 8-second vertical silent 3D cartoon scene using the provided baby image.

IMPORTANT:
Keep the exact same baby character.
Do not change the face, large hazel eyes, curly brown hair,
skin tone, age, body proportions or clothing.

Scene:
The baby wants to reach the colorful toy car.

He crawls toward it.
He stretches his little hands.
The toy rolls slightly farther away.

The baby stops and looks surprised.
Then he makes a funny determined expression.

Use exaggerated but natural baby body language.

The baby does NOT speak.
No dialogue.
No lip-sync.
No subtitles.
No text.
No other people.

Cute expressive 3D cartoon animation.
Warm playful atmosphere.
Vertical 9:16 composition.
"""
    },

    {
        "name": "scene
