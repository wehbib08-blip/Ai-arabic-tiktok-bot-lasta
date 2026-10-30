AI Viral Video Bot — v1
What this version does
Reads Google's public Google Trends RSS feed for the configured region.
Uses Gemini to choose one original AI-video idea and create its prompt, caption and hashtags.
Uses Gemini Omni Flash (gemini-omni-1.1-flash) to generate a vertical 9:16 video.
Optionally extends the clip once (default: up to 20 seconds total).
Saves tiktok_video.mp4 and video_metadata.json as a GitHub Actions artifact.
Important limitations
Google Trends is a search-interest signal, not TikTok's private trend analytics.
If the RSS feed is unavailable, the bot chooses from broad evergreen AI-video categories and does not claim the idea is currently trending.
This version does not publish to TikTok. Review the generated video first. TikTok publishing will be a separate integration after the generation test succeeds.
The first run should be started manually from GitHub Actions. Confirm your Google AI API key has access to Gemini Omni Flash and billing/quota is available.
Files to place in your repository
tiktok_bot.py -> repository root, replacing the old story bot.
requirements.txt -> repository root.
tiktok.yml -> .github/workflows/tiktok.yml.
Remove old story-only files from the workflow's required path only after confirming no other workflow uses them. The new bot no longer requires character_bible.json, master_prompt.txt, baby.png, or baby_grandma.png.
GitHub secret
Create/keep this repository secret:
GEMINI_API_KEY
Settings
The workflow runs once daily at 06:00 UTC and can also be run manually.
TREND_GEO=US
VIDEO_EXTENSIONS=1 (set to 0 to skip the extension and generate one short clip)
GEMINI_TEXT_MODEL=gemini-3.8-flash
GEMINI_VIDEO_MODEL=gemini-omni-1.1-flash
06:00 UTC corresponds to 08:00 in Lebanon during standard time and 09:00 during daylight-saving time.
