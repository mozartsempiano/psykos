# Psykos

**[Psykos](https://bsky.app/profile/psykos.bsky.social)** is an automated bot that fetches random images from Tumblr, analyzes their aesthetics, and posts them on Bluesky. It uses advanced APIs and libraries to ensure an efficient and secure experience.

## Features

- Fetches random images from Tumblr blogs.
- Filters images based on aesthetics using the CLIP model.
- Detects unwanted themes in captions and images.
- Publishes images on Bluesky with clean captions and alt text.
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
   ```

4. Make sure Tesseract OCR is installed and set the path in the `config.py` file:
   ```python
   TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

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
