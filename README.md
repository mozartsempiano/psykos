# Psykos

**[Psykos](https://bsky.app/profile/psykos.bsky.social)** is an automated bot that fetches random images from Tumblr, analyzes their aesthetics, and posts them on Bluesky. When Instagram credentials are configured, it also fetches Tumblr video posts and publishes them as Instagram Reels.

## Features

- Fetches random images from Tumblr blogs.
- Filters images based on aesthetics using the CLIP model.
- Detects unwanted themes in captions and images.
- Publishes images on Bluesky with clean captions and alt text.
- Optionally publishes Tumblr videos as Instagram Reels.
- Logs history of approved and rejected posts.

## Installation

### Prerequisites

- Python 3.8 or higher.
- Tesseract OCR installed ([Installation Guide](https://github.com/tesseract-ocr/tesseract)).
- Credentials for Tumblr and Bluesky APIs.

### Step by step

1. Clone this repository:

   ```bash
   git clone https://github.com/seu-usuario/psykos.git
   cd psykos
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create and configure the `.env` file with your credentials:

   ```properties
   BLUESKY_HANDLE=your_user.bsky.social
   BLUESKY_APP_PASSWORD=your_app_password ([Get one here](https://bsky.app/settings/app-passwords))
   TUMBLR_CONSUMER_KEY=your_consumer_key
   TUMBLR_SECRET_KEY=your_secret_key
   INSTAGRAM_ACCOUNT_ID=your_instagram_professional_account_id
   INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
   INSTAGRAM_REEL_BLOGS=your-owned-blog,licensed-source
   ```

4. Make sure Tesseract OCR is installed and set the path in the `config.py` file:
   ```python
   TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

### Instagram Reels

Instagram publishing is optional. Leave `INSTAGRAM_ACCOUNT_ID` and
`INSTAGRAM_ACCESS_TOKEN` unset to keep the existing Bluesky-only behavior. Set
both values and `INSTAGRAM_REEL_BLOGS` to enable one Reel attempt per bot
cycle. The Reel blog list is required and restricts video selection to the
named Tumblr sources; include only blogs whose videos you own or are authorized
to republish. These blogs must also appear in `tumblrs.txt`.
Reel attempts respect the bot interval with a 15-minute minimum, keeping the
maximum below Instagram's 100 API-published posts per rolling 24 hours.

The account must be a professional Instagram account and the Meta app/token
must have the content-publishing permissions required by the selected login
flow. See Meta's [Content Publishing guide](https://developers.facebook.com/documentation/instagram-platform/content-publishing)
for account, permission, and app setup requirements. The bot uses Facebook
Login's Graph API endpoint; the API host and version are fixed in the code.

The bot requests Tumblr's video post type and sends the post's direct HTTPS
`video_url` to Meta. That URL must be publicly reachable by Meta while the
video is processed. Posts without a direct video URL are skipped. This flow
filters by media type; it does not run the image CLIP aesthetic analysis on
video frames.

## Usage

1. Create and add the Tumblr blog titles to the `tumblrs.txt` file, separated by commas:

   ```
   blog1, blog2, blog3
   ```

2. Run the bot:

   ```bash
   python main.py
   ```

3. The bot will fetch images, apply filters, and post to Bluesky automatically.

## Contributing

Contributions are welcome! To contribute:

1. Fork the project.
2. Create a branch for your feature:
   ```bash
   git checkout -b my-feature
   ```
3. Make your changes and commit:
   ```bash
   git commit -m "Feature description"
   ```
4. Push your changes:
   ```bash
   git push origin my-feature
   ```
5. Open a Pull Request.
6. 
## License

This project is licensed under the [GNU GPLv3 License](LICENSE).
