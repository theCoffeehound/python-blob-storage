from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import os
import uuid
import jwt
import random
import string
from dotenv import load_dotenv
from datetime import datetime
import secrets


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load sensitive information from .env file
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')  # MongoDB URI (default local)
DB_NAME = os.getenv('DB_NAME', 'python_blob_storage')  # Database name
JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret')  # Secret for JWT token

# Setup MongoDB connection
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]  # Connect to the database
files_collection = db['files']  # Collection to store file metadata
api_keys_collection = db['api_keys']  # Collection to store API keys

# Folder where the files will be stored
UPLOAD_FOLDER = 'blobs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to verify JWT token and get user info
def verify_jwt(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return decoded  # Decoded token contains user info, e.g., userId
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

@app.route('/api/roll-api-key', methods=['POST'])
def roll_api_key_endpoint():
    # Step 1: Verify JWT Token
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'message': 'Unauthorized: Missing or Invalid JWT'}), 401

    jwt_token = token.split(' ')[1]
    user_info = verify_jwt(jwt_token)
    if not user_info:
        return jsonify({'message': 'Unauthorized: Invalid JWT Token'}), 401

    user_id = user_info['user_id']

    # Step 2: Generate a new API key
    new_api_key = secrets.token_urlsafe(32)
    
    # Step 3: Store it with the user_id
    api_keys_collection.update_one(
        {'user_id': user_id},
        {'$set': {
            'api_key': new_api_key,
            'rolled_at': datetime.utcnow(),
            'rolled_by': user_id  # Store who rolled it
        }},
        upsert=True
    )

    return jsonify({'message': 'API key rolled successfully', 'newApiKey': new_api_key}), 200


@app.route('/api/upload', methods=['POST'])
def upload_file():

    # Step 1: Verify JWT Token
    token = request.headers.get('Authorization')
    print("Received Token:", token)

    if not token or not token.startswith('Bearer '):
        return jsonify({'message': 'Unauthorized: Missing or Invalid JWT'}), 401
    jwt_token = token.split(' ')[1]  # Extract JWT from the header
    print("JWT GOING TO THE verify_token is:", jwt_token)
    # Verify JWT and get user info (e.g., userId)
    user_info = verify_jwt(jwt_token)
    if not user_info:
        return jsonify({'message': 'Unauthorized: Invalid JWT Token'}), 401

    user_id = user_info['user_id']  # Assuming JWT contains the 'user_id' claim

    # Step 2: Verify API Key
    api_key = request.headers.get('x-api-key')
    if not api_key or not api_keys_collection.find_one({'api_key': api_key, 'user_id': user_id}):
        return jsonify({'message': 'Unauthorized: Invalid API Key'}), 401
    else:
        print("api key valid")

    # Step 3: Ensure file is provided in the request
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    # Step 4: Generate a unique filename based on userId and UUID
    file_extension = os.path.splitext(file.filename)[1]
    user_folder = os.path.join("blobs", user_id)  # Create path like 'blobs/testuser/'

    # Create the folder if it doesn't exist
    os.makedirs(user_folder, exist_ok=True)

    # Final path for the file
    unique_filename = f"{str(uuid.uuid4())}{file_extension}"
    full_path = os.path.join(user_folder, unique_filename)
    file.seek(0, os.SEEK_END)          # Move to end of file
    file_size = file.tell()            # Get current position = size in bytes
    file.seek(0)                       # Reset to beginning for saving or reading

    # Step 6: Store file metadata in MongoDB
    file_metadata = {
        "user_id": user_id,
        "original_name": file.filename,
        "storage_name": unique_filename,  # This should be just the generated filename (UUID + extension)
        "path": full_path,  # Full relative path like "blobs/<user_id>/<filename>"
        "url": f"/api/fetch/{str(unique_filename)}",  # Use UUID as part of the URL
        "size_bytes": file_size,
        "uploaded_at": datetime.utcnow()
    }

    # Save the file
    file.save(full_path)
    files_collection.insert_one(file_metadata)

    # Step 7: Return the file URL (or file path)
    return jsonify({'message': 'File uploaded successfully', 'fileUrl': file_metadata['url']}), 200

@app.route('/api/fetch/<string:uuid>', methods=['GET'])
def fetch_file(uuid):
    
    # Step 1: Auth
    token = request.headers.get('Authorization')

    if not token or not token.startswith('Bearer '):
        return jsonify({'message': 'Unauthorized'}), 401
    
    jwt_token = token.split(' ')[1]
    user_info = verify_jwt(jwt_token)
    
    if not user_info:
        return jsonify({'message': 'Unauthorized: Invalid JWT'}), 401

    user_id = user_info['user_id']

    api_key = request.headers.get('x-api-key')

    if not api_key or not api_keys_collection.find_one({'api_key': api_key, 'user_id': user_id}):
        return jsonify({'message': 'Unauthorized: Invalid API Key'}), 401
    else:
        print("api key valid")

    # Step 2: Get path from DB
    file_doc = files_collection.find_one({
        "storage_name": uuid,
        "user_id": user_id
    })

    if not file_doc:
        return jsonify({'message': 'File not found'}), 404

    file_path = file_doc['path']
    directory = os.path.dirname(file_path)
    actual_file = os.path.basename(file_path)

    return send_from_directory(directory, actual_file)


@app.route('/api/list', methods=['GET'])
def list_files():
    
    # Step 1: Verify JWT Token
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'message': 'Unauthorized: Missing or Invalid JWT'}), 401

    jwt_token = token.split(' ')[1]
    user_info = verify_jwt(jwt_token)
    if not user_info:
        return jsonify({'message': 'Unauthorized: Invalid JWT Token'}), 401

    user_id = user_info['user_id']

    # Step 2: Check API Key
    api_key = request.headers.get('x-api-key')
    if not api_key or not api_keys_collection.find_one({'api_key': api_key, 'user_id': user_id}):
        return jsonify({'message': 'Unauthorized: Invalid API Key'}), 401


    # Step 3: Fetch user's files from MongoDB
    user_files = files_collection.find({'user_id': user_id})
    files = [{
        'original_name': file['original_name'],
        'url': file['url'],
        'size_bytes': file['size_bytes'],
        'uploaded_at': file['uploaded_at']
    } for file in user_files]

    return jsonify({'files': files}), 200

if __name__ == '__main__':
    app.run(debug=True)
