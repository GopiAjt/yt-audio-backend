from flask import Flask, request, jsonify
from pytube import YouTube
import ffmpeg
import os
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/download_audio', methods=['POST'])
def download_audio():
    data = request.json
    youtube_url = data.get('youtube_url')
    output_path = './downloads'

    if not youtube_url:
        logging.error("YouTube URL is required")
        return jsonify({"error": "YouTube URL is required"}), 400

    try:
        logging.info(f"Starting download for URL: {youtube_url}")
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_stream.download(filename='temp_audio')

        logging.info("Download completed. Converting to MP3 format.")
        input_audio = ffmpeg.input('temp_audio')
        output_audio = ffmpeg.output(input_audio, os.path.join(output_path, yt.title + '.mp3'))
        ffmpeg.run(output_audio)

        logging.info("Conversion completed. Cleaning up temporary files.")
        os.remove('temp_audio')

        logging.info(f"Audio downloaded successfully: {yt.title}.mp3")
        return jsonify({"message": f"Audio downloaded successfully: {yt.title}.mp3"}), 200

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.makedirs('./downloads', exist_ok=True)
    app.run(debug=True)