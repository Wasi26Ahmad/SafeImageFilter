from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
import opennsfw2 as n2  # Import OpenNSFW2 for nudity detection
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
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    if result['is_nude']:
        uploaded_images[filename] = {'blurred_image': result['blurred_image'], 'password': SECRET_PASSWORD}
        return jsonify({
            "message": "Nudity detected and image blurred.",
            "blurred_image": result['blurred_image']
        }), 200
    else:
        return jsonify({
            "message": "No nudity detected in the image.",
            "original_image": filepath
        }), 200

# Function to detect and classify nudity using OpenNSFW2
def detect_and_classify(image_path):
    image = cv2.imread(image_path)

    # Resize the image to 224x224 (model's input size)
    image_resized = cv2.resize(image, (224, 224))
    image_preprocessed = np.expand_dims(image_resized, axis=0) / 255.0

    # Classify the image using OpenNSFW2 model
    prediction = n2.predict_image(image_path)

    is_nude = False
    blurred_image_path = None

    # If nudity is detected (confidence > 0.8), blur the image
    if prediction > 0.8:  # Assuming the output is a probability between 0 and 1
        is_nude = True
        blurred_image = cv2.GaussianBlur(image, (99, 99), 30)
        blurred_image_path = image_path.replace('.jpg', '_blurred.jpg')
        cv2.imwrite(blurred_image_path, blurred_image)  # Save the blurred image

    return {
        'is_nude': is_nude,
        'confidence': prediction,
        'blurred_image': blurred_image_path
    }

# Route to unblur the image after password check
@app.route('/unblur_image', methods=['POST'])
def unblur_image():
    data = request.json
    filename = data.get('filename')
    password = data.get('password')

    if password == uploaded_images.get(filename, {}).get('password'):
        original_image_path = filename.replace('_blurred', '')
        return jsonify({
            "message": "Password correct. Here is the original image.",
            "original_image": original_image_path
        }), 200
    else:
        return jsonify({"error": "Incorrect password!"}), 400

if __name__ == '__main__':
    app.run(debug=True)
