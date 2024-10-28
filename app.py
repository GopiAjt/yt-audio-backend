import os
import re
import io
import logging
import ffmpeg
from flask import Flask, request, jsonify, send_file
from pytube import YouTube, exceptions as pytube_exceptions
from flask_cors import CORS
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# YouTube URL validation pattern
YOUTUBE_URL_PATTERN = r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'

def validate_youtube_url(url):
    return re.match(YOUTUBE_URL_PATTERN, url)

def clean_youtube_url(url):
    parsed_url = urlparse(url)
    return urlunparse(parsed_url._replace(query=""))

@app.route('/', methods=['GET'])
def hello():
    return "Service is running"

@app.route('/download_audio', methods=['POST'])
def download_audio():
    data = request.json
    youtube_url = clean_youtube_url(data.get('youtube_url'))

    # Validate the YouTube URL
    if not youtube_url or not validate_youtube_url(youtube_url):
        logging.error("Invalid or missing YouTube URL")
        return jsonify({"error": "A valid YouTube URL is required"}), 400

    temp_audio = 'temp_audio.mp4'  # Specify the file extension for better ffmpeg compatibility

    try:
        # Try to get the YouTube video
        logging.info(f"Starting download for URL: {youtube_url}")
        yt = YouTube(youtube_url)
        
        # Filter for audio-only streams
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            logging.error("No audio stream found for this video")
            return jsonify({"error": "No audio stream available for this URL"}), 400

        # Download the audio stream
        audio_stream.download(filename=temp_audio)
        logging.info("Download completed. Starting MP3 conversion.")

        # Convert the downloaded file to MP3 format using ffmpeg
        input_audio = ffmpeg.input(temp_audio)
        output_buffer = io.BytesIO()

        # Execute ffmpeg conversion to MP3
        process = (
            ffmpeg
            .output(input_audio, 'pipe:1', format='mp3')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        output, error = process.communicate()

        if process.returncode != 0:
            error_message = error.decode('utf8')
            logging.error(f"FFmpeg error: {error_message}")
            return jsonify({"error": "Error during audio conversion", "details": error_message}), 500

        output_buffer.write(output)
        output_buffer.seek(0)

        logging.info(f"Audio downloaded and converted successfully: {yt.title}.mp3")
        return send_file(output_buffer, as_attachment=True, download_name=f"{yt.title}.mp3", mimetype="audio/mpeg")

    except pytube_exceptions.VideoUnavailable:
        logging.error("The requested video is unavailable.")
        return jsonify({"error": "The requested video is unavailable."}), 404
    except pytube_exceptions.RegexMatchError:
        logging.error("The provided URL does not match any known YouTube video.")
        return jsonify({"error": "Invalid YouTube URL pattern."}), 400
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    finally:
        # Ensure the temporary file is deleted
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

if __name__ == '__main__':
    app.run(debug=True)
