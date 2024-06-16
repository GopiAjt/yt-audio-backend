from flask import Flask, request, jsonify
from pytube import YouTube
import ffmpeg
import os

app = Flask(__name__)

@app.route('/download_audio', methods=['POST'])
def download_audio():
    data = request.json
    youtube_url = data.get('youtube_url')
    output_path = './downloads'

    if not youtube_url:
        return jsonify({"error": "YouTube URL is required"}), 400

    try:
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_stream.download(filename='temp_audio')

        input_audio = ffmpeg.input('temp_audio')
        output_audio = ffmpeg.output(input_audio, os.path.join(output_path, yt.title + '.mp3'))
        ffmpeg.run(output_audio)

        os.remove('temp_audio')

        return jsonify({"message": f"Audio downloaded successfully: {yt.title}.mp3"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.makedirs('./downloads', exist_ok=True)
    app.run(debug=True)
