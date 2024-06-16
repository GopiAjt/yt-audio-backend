from flask import Flask, request, jsonify, send_file
from pytube import YouTube
import ffmpeg
import os
import logging
import io
import subprocess

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/download_audio', methods=['POST'])
def download_audio():
    data = request.json
    youtube_url = data.get('youtube_url')

    if not youtube_url:
        logging.error("YouTube URL is required")
        return jsonify({"error": "YouTube URL is required"}), 400

    try:
        logging.info(f"Starting download for URL: {youtube_url}")
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        temp_audio = 'temp_audio'
        audio_stream.download(filename=temp_audio)

        logging.info("Download completed. Converting to MP3 format.")
        input_audio = ffmpeg.input(temp_audio)
        output_buffer = io.BytesIO()

        # Use ffmpeg.run_async to capture output in memory
        process = (
            ffmpeg
            .output(input_audio, 'pipe:1', format='mp3')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        output, error = process.communicate()

        if process.returncode != 0:
            logging.error(f"FFmpeg error: {error.decode('utf8')}")
            return jsonify({"error": "Error during audio conversion"}), 500

        output_buffer.write(output)
        output_buffer.seek(0)

        # Clean up temporary file
        os.remove(temp_audio)

        logging.info(f"Audio downloaded successfully: {yt.title}.mp3")
        return send_file(output_buffer, as_attachment=True, download_name=f"{yt.title}.mp3", mimetype="audio/mpeg")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
