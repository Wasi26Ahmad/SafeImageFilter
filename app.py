from flask import Flask, render_template, request, jsonify, url_for
import os
import cv2
from nudenet import NudeDetector  # Import NudeNet for nudity detection
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secret password for unblurring
SECRET_PASSWORD = "secret123"

# Mock data for user management (you can integrate a database later)
users = {
    "user1": {"password": "password123"},
    "user2": {"password": "mypassword456"}
}

# Temporary store for images
uploaded_images = {}

# Configure the upload folder
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = 'static/'  # Path for serving static files
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

# Initialize the NudeDetector
detector = NudeDetector()

@app.route('/')
def index():
    return render_template('index.html')

# Route to update password
@app.route('/update_password', methods=['POST'])
def update_password():
    data = request.json
    username = data.get('username')
    new_password = data.get('new_password')

    # Update the password if the user exists
    if username in users:
        users[username]['password'] = new_password
        return jsonify({"message": "Password updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Route to add new user
@app.route('/add_new_user', methods=['POST'])
def add_new_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Add new user
    if username in users:
        return jsonify({"error": "User already exists"}), 400
    else:
        users[username] = {"password": password}
        return jsonify({"message": "User added successfully"}), 200

# Route for nudity detection and blurring the image
@app.route('/detect_nudity', methods=['POST'])
def detect_nudity():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Process the image and classify
    result = detect_and_classify(filepath)

    # If nudity detected, blur image
    if result['is_nude']:
        blurred_image_path = os.path.join(app.config['STATIC_FOLDER'], f"blurred_{filename}")
        uploaded_images[filename] = {'blurred_image': blurred_image_path, 'password': SECRET_PASSWORD}
        cv2.imwrite(blurred_image_path, result['blurred_image'])  # Save the blurred image in static folder
        return jsonify({
            "message": "Nudity detected and image blurred.",
            "blurred_image": url_for('static', filename=f'blurred_{filename}'),
            "original_image": url_for('static', filename=filename)
        }), 200
    else:
        return jsonify({
            "message": "No nudity detected in the image.",
            "original_image": url_for('static', filename=filename)
        }), 200

# Function to detect and classify nudity using NudeNet
def detect_and_classify(image_path):
    image = cv2.imread(image_path)

    # Use NudeNet's detector to detect nudity in the image
    detections = detector.detect(image_path)

    print("Detection Results:", detections)  # Debugging log

    is_nude = False
    blurred_image = None

    # Define the classes that indicate nudity
    nudity_classes = [
        'FEMALE_BREAST_EXPOSED',
        'FEMALE_GENITALIA_EXPOSED',
        'BUTTOCKS_EXPOSED',
        'MALE_GENITALIA_EXPOSED',
        'ANUS_EXPOSED',
        'BELLY_EXPOSED'
    ]
    confidence_threshold = 0.8

    # Ensure we are checking for the presence of the correct 'class' and 'score'
    for detection in detections:
        if 'class' in detection and 'score' in detection:
            print(f"Class: {detection['class']}, Score: {detection['score']}")  # Debugging
            # Check if the detected class is related to nudity and if the confidence score is high enough
            if detection['class'] in nudity_classes and detection['score'] > confidence_threshold:
                is_nude = True
                blurred_image = cv2.GaussianBlur(image, (99, 99), 30)  # Apply Gaussian Blur
                break  # No need to check further if nudity is detected

    return {
        'is_nude': is_nude,
        'blurred_image': blurred_image
    }

@app.route('/unblur_image', methods=['POST'])
def unblur_image():
    data = request.json
    filename = data.get('filename')
    password = data.get('password')

    if password == uploaded_images.get(filename, {}).get('password'):
        original_image_path = os.path.join(app.config['STATIC_FOLDER'], filename)
        return jsonify({
            "message": "Password correct. Here is the original image.",
            "original_image": url_for('static', filename=filename)
        }), 200
    else:
        return jsonify({"error": "Incorrect password!"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

