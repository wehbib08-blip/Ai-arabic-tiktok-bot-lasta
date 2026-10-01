name: Pixabay Video Test

on:
  workflow_dispatch:

jobs:
  test-pixabay:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install requests
        run: |
          python -m pip install --upgrade pip
          pip install requests

      - name: Test Pixabay
        env:
          PIXABAY_API_KEY: ${{ secrets.PIXABAY_API_KEY }}
        run: |
          python pixabay_test.py

      - name: Upload test video
        uses: actions/upload-artifact@v4
        with:
          name: pixabay-test-video
          path: test_video.mp4
