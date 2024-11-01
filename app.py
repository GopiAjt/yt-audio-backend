import os
import re
import io
import logging
from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
from flask_cors import CORS

app = Flask(__name__)
CORS(app, expose_headers=['X-Title'])

# Configure logging
logging.basicConfig(level=logging.INFO)

# YouTube URL validation pattern
YOUTUBE_URL_PATTERN = r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'

def validate_youtube_url(url):
    return re.match(YOUTUBE_URL_PATTERN, url)

def download_audio_from_youtube(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp_audio.%(ext)s',  # Temporary filename
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        audio_file_path = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
    
    return audio_file_path, info_dict.get('title', 'audio')

@app.route('/', methods=['GET'])
def hello():
    return "Service is running"

@app.route('/download_audio', methods=['POST'])
def download_audio():
    data = request.json
    youtube_url = data.get('youtube_url')

    if not youtube_url or not validate_youtube_url(youtube_url):
        logging.error("Invalid or missing YouTube URL")
        return jsonify({"error": "A valid YouTube URL is required"}), 400

    try:
        logging.info(f"Starting download for URL: {youtube_url}")
        audio_file_path, title = download_audio_from_youtube(youtube_url)

        # Read file into memory for sending as response
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = io.BytesIO(audio_file.read())
        audio_data.seek(0)

        # Clean up the downloaded file
        os.remove(audio_file_path)

        logging.info(f"Audio downloaded and converted successfully: {title}.mp3")
        
        # Create response
        response = send_file(audio_data, as_attachment=True, download_name=f"{title}.mp3", mimetype="audio/mpeg")
        
        # Add the title to the response headers
        response.headers["X-Title"] = title  # Make sure this line is present

        return response

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
