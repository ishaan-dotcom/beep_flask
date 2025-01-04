# app.py
from flask import Flask, request, render_template_string, send_from_directory, jsonify
from gradio_client import Client, handle_file
import os
import logging

# Optional: For audio format conversion
try:
    from pydub import AudioSegment
    AUDIO_CONVERSION = True
except ImportError:
    AUDIO_CONVERSION = False

app = Flask(__name__)

# Initialize the Gradio API client for the specified model/endpoint
gradio_client = Client("ishaank123/BEEPwhisper")

# Configure logging for debugging purposes
logging.basicConfig(level=logging.DEBUG)

# Directory to store temporary audio files
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# HTML template with enhanced GUI features
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Scam Call Detector with BEEP</title>
    <style>
        /* Base Styles */
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #1e1e2f; /* Dark navy background */
            color: #ffffff;
        }
        header {
            text-align: center;
            padding: 20px;
            background-color: #141420;
        }
        header h1 {
            margin: 0;
            font-size: 2em;
            color: #ff9800; /* Orange accent for title */
        }
        header p {
            margin: 5px 0 20px 0;
            color: #cccccc;
        }
        .container {
            display: flex;
            justify-content: center;
            padding: 20px;
        }
        .upload-section, .output-section {
            flex: 1;
            margin: 10px;
        }
        .upload-section {
            max-width: 400px;
            padding: 20px;
            background-color: #2a2a40;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }
        .upload-section h2 {
            color: #ff9800;
        }
        .upload-area {
            border: 2px dashed #555;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            color: #aaaaaa;
            margin-bottom: 20px;
            position: relative;
            transition: border-color 0.3s, color 0.3s;
        }
        .upload-area:hover {
            border-color: #ff9800;
            color: #ffffff;
            cursor: pointer;
        }
        .upload-area input[type="file"] {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }
        .buttons {
            display: flex;
            justify-content: space-between;
        }
        .buttons button {
            width: 48%;
            padding: 10px;
            border: none;
            border-radius: 4px;
            font-size: 1em;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .buttons .clear-btn {
            background-color: #555555;
            color: #ffffff;
        }
        .buttons .clear-btn:hover {
            background-color: #777777;
        }
        .buttons .submit-btn {
            background-color: #ff9800;
            color: #ffffff;
        }
        .buttons .submit-btn:hover {
            background-color: #e68900;
        }
        .additional-features {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
        }
        .additional-features img {
            width: 40px;
            height: 40px;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .additional-features img:hover {
            transform: scale(1.1);
        }
        .output-section {
            max-width: 600px;
            padding: 20px;
            background-color: #2a2a40;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            height: fit-content;
        }
        .output-box {
            width: 100%;
            min-height: 150px;
            background-color: #1e1e2f;
            border: 1px solid #555555;
            border-radius: 4px;
            color: #ffffff;
            padding: 10px;
            margin-bottom: 20px;
            resize: none;
            font-size: 1em;
        }
        .output-label {
            margin-bottom: 5px;
            font-weight: bold;
            color: #ff9800;
        }
        /* Loading Spinner Styles */
        .spinner {
            display: none; /* Hidden by default */
            border: 4px solid #f3f3f3; /* Light grey */
            border-top: 4px solid #ff9800; /* Orange */
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        /* Audio Player Styles */
        .audio-player {
            margin-bottom: 20px;
            text-align: center;
        }
        .audio-player audio {
            width: 100%;
            outline: none;
        }
    </style>
</head>
<body>
    <header>
        <h1>Scam Call Detector with BEEP</h1>
        <p>Upload your recorded call to see if it is a scam or not. Stay Safe, Stay Secure.</p>
    </header>
    
    <div class="container">
        <div class="upload-section">
            <h2>Audio</h2>
            <form id="uploadForm" method="POST" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea">
                    <p>Drop Audio Here - or - Click to Upload</p>
                    <input type="file" name="audioFile" accept="audio/*" required>
                </div>
                <div class="buttons">
                    <button type="reset" class="clear-btn">Clear</button>
                    <button type="submit" class="submit-btn">Submit</button>
                </div>
            </form>
            <div class="additional-features">
                <img src="https://img.icons8.com/ios-filled/50/ffffff/upload.png" alt="Upload Icon" title="Upload Audio">
                <img src="https://img.icons8.com/ios-filled/50/ffffff/microphone.png" alt="Microphone Icon" title="Record Audio">
            </div>
            <!-- Loading Spinner -->
            <div class="spinner" id="loadingSpinner"></div>
            <!-- Audio Player -->
            <div class="audio-player" id="audioPlayerContainer" style="display:none;">
                <p>Uploaded Audio:</p>
                <audio controls id="audioPlayer">
                    Your browser does not support the audio element.
                </audio>
            </div>
        </div>
        
        <div class="output-section">
            <div>
                <div class="output-label">Output 0 (Transcribed Text):</div>
                <textarea class="output-box" readonly>{{ output0 }}</textarea>
            </div>
            <div>
                <div class="output-label">Output 1 (Generated Content):</div>
                <textarea class="output-box" readonly>{{ output1 }}</textarea>
            </div>
        </div>
    </div>
    
    <script>
        // JavaScript to handle the loading spinner and audio player
        const uploadForm = document.getElementById('uploadForm');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const audioPlayerContainer = document.getElementById('audioPlayerContainer');
        const audioPlayer = document.getElementById('audioPlayer');
        const uploadArea = document.getElementById('uploadArea');

        uploadForm.addEventListener('submit', function() {
            // Show the loading spinner when the form is submitted
            loadingSpinner.style.display = 'block';
        });

        // Show the audio player when a file is selected
        uploadArea.querySelector('input[type="file"]').addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const fileURL = URL.createObjectURL(file);
                audioPlayer.src = fileURL;
                audioPlayerContainer.style.display = 'block';
            } else {
                audioPlayerContainer.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    output0 = ""
    output1 = ""

    if request.method == "POST":
        try:
            # Retrieve the uploaded audio file
            audio_file = request.files.get("audioFile")
            if not audio_file:
                raise ValueError("No file uploaded.")

            # Secure the filename
            filename = os.path.basename(audio_file.filename)
            temp_path = os.path.join(TEMP_DIR, filename)
            audio_file.save(temp_path)
            logging.debug(f"Saved uploaded file to {temp_path}")

            # Optional: Convert MP3 to WAV if required by the API
            if AUDIO_CONVERSION and filename.lower().endswith(".mp3"):
                wav_path = os.path.splitext(temp_path)[0] + ".wav"
                audio = AudioSegment.from_mp3(temp_path)
                audio.export(wav_path, format="wav")
                logging.debug(f"Converted MP3 to WAV at {wav_path}")
                # Update the path to the converted file
                temp_path = wav_path

            # Call the Gradio API to process the audio file
            result = gradio_client.predict(
                audio=handle_file(temp_path),
                api_name="/predict"
            )
            logging.debug(f"Received result from Gradio API: {result}")

            # Extract the results
            output0, output1 = result[0], result[1]

        except Exception as e:
            logging.error(f"Error during file processing: {e}")
            output0 = "An error occurred while processing the audio file."
            output1 = str(e)

        finally:
            # Clean up by removing the temporary file(s)
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logging.debug(f"Removed temporary file {temp_path}")
                # Also remove WAV file if conversion was done
                if AUDIO_CONVERSION and filename.lower().endswith(".mp3"):
                    wav_path = os.path.splitext(temp_path)[0] + ".wav"
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                        logging.debug(f"Removed temporary WAV file {wav_path}")
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}")

    return render_template_string(html_template, output0=output0, output1=output1)

@app.route('/temp_audio/<filename>')
def uploaded_file(filename):
    """Route to serve uploaded audio files."""
    return send_from_directory(TEMP_DIR, filename)

if __name__ == "__main__":
    # Use the PORT environment variable if available (useful for deployment)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)