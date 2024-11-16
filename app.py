import os
from flask import Flask, request, send_file, render_template, redirect, url_for
from gtts import gTTS
from datetime import datetime

app = Flask(__name__)

# Set the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to check if the file is an allowed type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to check if the file is a generated audio file (based on naming convention)
def is_generated_file(filename):
    return filename.startswith("voice_")  # Check if it follows the "voice_" pattern

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    uploaded_filename = None  # Store the uploaded filename for text-based voice creation
    text_input_display = False  # Flag to show text input box after file upload
    
    # List only generated audio files (those that start with "voice_")
    audio_files = [
        f for f in os.listdir(UPLOAD_FOLDER) 
        if allowed_file(f) and is_generated_file(f)  # Filter out uploaded files
    ]
    
    if request.method == 'POST':
        if 'voicefile' not in request.files:
            message = "No file part"
        else:
            file = request.files['voicefile']
            
            if file.filename == '':
                message = "No selected file"
            elif file and allowed_file(file.filename):
                if len(file.read()) > MAX_FILE_SIZE:
                    message = "Oops, this file is too big! Please try again."
                else:
                    file.seek(0)  # Reset the file pointer after reading its size
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filename)
                    message = "File uploaded successfully! You can now enter text for voice creation."
                    uploaded_filename = file.filename  # Save the uploaded filename
                    text_input_display = True  # Show the text input box
            else:
                message = "Oops, this file is too big or not supported! Please try again."

    return render_template('index.html', message=message, audio_files=audio_files, text_input_display=text_input_display, uploaded_filename=uploaded_filename)

@app.route('/create_voice', methods=['POST'])
def create_voice():
    text = request.form['text']
    uploaded_filename = request.form['uploaded_filename']
    
    # Use Google TTS to generate speech from text
    tts = gTTS(text, lang='en')
    
    # Get the current time and date for the filename
    current_time = datetime.now()
    time_str = current_time.strftime("%H-%M-%S")  # Format time as hh-mm-ss
    date_str = current_time.strftime("%d-%m")  # Format date as dd-mm (to avoid slash)

    # Create a unique filename using the current time and date
    new_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"voice_{date_str}_{time_str}.mp3")
    
    tts.save(new_filename)  # Save the new voice file
    
    # Redirect to the index to display the list of files
    return redirect('/')

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
