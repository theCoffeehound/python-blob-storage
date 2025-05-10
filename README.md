# python-blob-storage

A minimal, secure Flask-based file storage service with support for user authentication using JWT and API keys. Files are stored in a local folder structure, and metadata is saved in MongoDB.


## 📚 Table of Contents

- [Requirements](#requirements)
- [Features](#features)
- [Folder Structure](#folder-structure)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [POST /api/upload](#post-apiupload)
  - [GET /api/fetch/:uuid](#get-apifetchuuid)
  - [GET /api/list](#get-apilist)
  - [GET /api/roll-api-key](#get-apiroll-api-key)
- [Notes](#notes)
- [Installation Instructions](#installation-instructions)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Create a virtual environment](#2-create-a-virtual-environment)
  - [3. Activate the virtual environment](#3-activate-the-virtual-environment)
  - [4. Install the dependencies](#4-install-the-dependencies)
  - [5. Set up environment variables](#5-set-up-environment-variables)
  - [6. Run the application](#6-run-the-application)
  - [7. Testing the endpoints](#7-testing-the-endpoints)


## Features

- Upload files with JWT and API key authentication
- Fetch individual files
- List all files uploaded by a user
- Roll and regenerate user-specific API keys
- Metadata tracked in MongoDB (original name, size, upload time, etc.)

## Requirements

- Python 3.8+
- MongoDB
- pip packages (install with requirements)

```bash
pip install -r requirements.txt
```

## Folder Structure

```
blobs/
  └── <user_id>/
        └── <uuid>.ext
```

## API Endpoints

### POST /api/upload

**Headers:**
- `Authorization: Bearer <jwt>` (JWT Token for user authentication)
- `x-api-key: <api-key>` (Valid API key)

**Form Data:**
- `file`: The file to be uploaded.

**Response:**

```json
{
  "message": "File uploaded successfully",
  "fileUrl": "/api/fetch/<uuid>"
}
```

### GET /api/fetch/:uuid

**Headers:**

- `Authorization: Bearer <jwt>` (JWT Token for user authentication)
- `x-api-key: <api-key>` (Valid API key)

**Path Parameters:** 
- `uuid` The unique identifier of the file.

**Response:**

- **200 OK:** File data successfully fetched.

- **404 Not Found:** File not found for the given uuid.

    ```json
    {
    "message": "File not found"
    }
    ```

### GET /api/list

**Headers:**

- `Authorization: Bearer <jwt>` (JWT Token for user authentication)
- `x-api-key: <api-key>` (Valid API key)

**Response:**

- **200 OK:** Files data successfully fetched.
    ```json
    {
        "files": [
            {
            "original_name": "blobby_hd.png",
            "url": "/api/fetch/45d4d374-503d-484a-a158-967be988b5b0.png",
            "size_bytes": 3765395,
            "uploaded_at": "2025-05-09T12:13:27.179+00:00"
            },
            {
            "original_name": "blobby_hd2.png",
            "url": "/api/fetch/45d4d374-503d-484a-a158-967be988b5b1.png",
            "size_bytes": 3821432,
            "uploaded_at": "2025-05-10T12:45:29.679+00:00"
            }
        ]
    }
    ```

### GET /api/roll-api-key

**Headers:**

- `Authorization: Bearer <jwt>` (JWT Token for user authentication)

**Response:**

- **200 OK:** Files data successfully fetched.
    ```json
    {
        "message": "API key rolled successfully",
        "newApiKey": "<new-api-key>"
    }
    ```


## Notes

JWTs must be generated separately (e.g., using a login service).

Files are saved locally. For production, you could adapt it to use cloud storage (AWS S3, Azure Blob, etc.).

This is a backend-only project.

## Installation Instructions

### 1. Clone the repository
    
Start by cloning the repository to your local machine:

```bash
git clone https://github.com/thecoffeehound/python-blob-storage.git
cd python-blob-storage
```

### 2. Create a virtual environment

It is recommended to create a virtual environment to manage dependencies:

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

On Linux/macOS:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 4. Install the dependencies

After activating the virtual environment, install the required dependencies:

```bash
pip install -r requirements.txt
```

If you don't have a requirements.txt file yet, you can manually install the dependencies using pip:

```bash
pip install Flask pymongo python-dotenv pyjwt
```

### 5. Set up environment variables

You need to configure environment variables for your app. Create a .env file in the project root and add the following variables:

```
MONGODB_URI=mongodb://localhost:27017  # MongoDB URI (adjust if using a remote instance)
DB_NAME=python_blob_storage  # Database name
JWT_SECRET=your_jwt_secret  # Secret for JWT token
```

Replace your_jwt_secret with a secure secret key for encoding and decoding JWT tokens.

### 6. Run the application

Now that everything is set up, you can run your Flask application:

```bash
python main.py
```
Your server should be running at http://127.0.0.1:5000.

### 7. Testing the endpoints

You can use tools like Postman or curl to test the API endpoints.

For example, to upload a file, you can use a POST request to http://127.0.0.1:5000/api/upload with the proper headers and a file in the body.