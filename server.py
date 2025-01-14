import time
import io
import random
import math
import re

from pydub import AudioSegment

from flask import Flask, current_app, request, send_from_directory, jsonify, url_for
from flask.helpers import redirect

import werkzeug.utils as werkzeug_utils

# Configuration
ALLOWED_EXTENSIONS = {'webm', 'mp3', 'wav', 'ogg', 'm4a'}
STATIC_FOLDER = 'static'

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max file size

class Audio:
    data: None | bytes = None
    filename: str = ''
    start_time: float = 0
    identifier: int = 0
    total_duration: float = 0

    def __init__(self, data: None | bytes, filename: str):
        self.data = data
        self.filename = filename
        self.start_time = time.time_ns() // 1_000_000
        self.identifier = 1 + math.floor(random.random() * 1_000_000)
        if (data):
            media = AudioSegment.from_file(io.BytesIO(data))
            if (not media):
                self.total_duration = -1
                print("no media")
                print(media)
            else:
                self.total_duration = len(media)


current_audio: Audio = Audio(None, '')

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the index.html file from the static folder."""
    return send_from_directory(STATIC_FOLDER, 'index.html')

@app.route('/favicon.ico')
def serve_favicon():
    """Serve Favicon files."""
    return send_from_directory(STATIC_FOLDER, 'favicon.ico')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    filename = re.sub(r'\.html.*$', '.html', filename)
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/music')
def serve_music():
    """Server music file from memory"""
    if not current_audio.data:
        return jsonify({'error': 'no file running'}), 200
    else:
        return werkzeug_utils.send_file(io.BytesIO(current_audio.data), request.environ, download_name=current_audio.filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    global current_audio
    # Check if the post request has the file part
    if 'audio-file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['audio-file']

    # If user does not select file, browser also submit an empty part without filename
    if file.filename == '' or not file.filename:
        return jsonify({'error': 'No selected file'}), 400

    # Check if file is allowed
    print(f"Got File: ${file}")
    if file and allowed_file(file.filename):
        # Save the file in memory
        current_audio = Audio(file.stream.read(), file.filename)
        print(f"CurrentAudio: {current_audio.filename}")
        return redirect(url_for('index'))

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/state', methods=["GET"])
def get_state():
    """Get current state of playback"""
    global current_audio

    return jsonify({'filename': current_audio.filename, 'start_time': current_audio.start_time, 'id': current_audio.identifier, 'server_time': time.time_ns() // 1_000_000, 'total_duration': current_audio.total_duration})

if __name__ == '__main__':
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
