from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route to display the upload form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle image upload and content detection
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Image processing to detect nudity
        result = detect_nudity(filepath)

        return jsonify(result)

    return jsonify({'error': 'Invalid file type'}), 400

# Function to detect nudity in the image
def detect_nudity(image_path):
    # Placeholder for model inference, using OpenCV or a pre-trained AI model
    image = cv2.imread(image_path)
    confidence = 0.85  # Example confidence level
    is_nude = False
    blurred_image = None

    # Detect nude portions (this is where you use a pre-trained model)
    # For simplicity, this part is simulated here
    if confidence > 0.8:
        is_nude = True
        # Blur the detected nude areas (in a real scenario, use detection model results to blur specific areas)
        blurred_image = cv2.GaussianBlur(image, (99, 99), 30)

    # Save the blurred image
    blurred_image_path = image_path.replace('.jpg', '_blurred.jpg')
    cv2.imwrite(blurred_image_path, blurred_image)

    return {
        'is_nude': is_nude,
        'confidence': confidence,
        'blurred_image': blurred_image_path
    }

if __name__ == '__main__':
    app.run(debug=True)
