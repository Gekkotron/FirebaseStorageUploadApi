import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage
import hashlib
from dotenv import load_dotenv
import google.auth.transport.requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'mp4'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
REQUEST_TIMEOUT = 15  # seconds

# Initialize Firebase Admin SDK
cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'credential.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

# Set custom timeout for Firebase storage operations
original_request = google.auth.transport.requests.Request


class TimeoutRequest(google.auth.transport.requests.Request):
    def __call__(self, *args, **kwargs):
        kwargs['timeout'] = REQUEST_TIMEOUT
        return original_request.__call__(self, *args, **kwargs)


google.auth.transport.requests.Request = TimeoutRequest

bucket = storage.bucket()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload file to Firebase Storage
    Accepts: jpg, jpeg, mp4 files
    Optional parameters:
      - folder (string): specify folder path in Firebase Storage
      - use_original_name (bool): use original filename instead of hash
      - deduplicate (bool): use content hash to avoid duplicates (default)
    Returns: JSON with file URL and metadata
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Only jpg, jpeg, and mp4 are supported'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB'}), 400
        
        # Get optional folder parameter
        folder = request.form.get('folder', '').strip()
        use_original_name = request.form.get(
            'use_original_name', 'false').lower() == 'true'
        
        # Generate filename based on strategy
        original_filename = file.filename or 'unnamed'
        if '.' in original_filename:
            extension = original_filename.rsplit('.', 1)[1].lower()
        else:
            extension = ''
        
        if use_original_name:
            # Use the original filename as-is
            unique_filename = original_filename
        else:
            # Calculate file hash for deduplication
            file.seek(0)
            file_hash = hashlib.sha256(file.read()).hexdigest()[:16]
            file.seek(0)
            unique_filename = f"{file_hash}.{extension}"
        
        # Construct storage path with folder if provided
        if folder:
            # Remove leading/trailing slashes and construct path
            folder = folder.strip('/')
            storage_path = f"{folder}/{unique_filename}"
        else:
            storage_path = unique_filename
        
        # Check if file already exists (only for hash-based naming)
        blob = bucket.blob(storage_path)
        if not use_original_name and blob.exists():
            # File with same content already exists, return existing URL
            blob.reload()
            return jsonify({
                'success': True,
                'message': 'File already exists',
                'data': {
                    'filename': unique_filename,
                    'storage_path': storage_path,
                    'original_filename': original_filename,
                    'size': file_size,
                    'content_type': file.content_type,
                    'url': blob.public_url
                }
            }), 200
        
        # Upload to Firebase Storage
        blob.upload_from_file(file, content_type=file.content_type)
        
        # Make the file publicly accessible (optional)
        blob.make_public()
        
        # Get public URL
        url = blob.public_url
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'data': {
                'filename': unique_filename,
                'storage_path': storage_path,
                'original_filename': original_filename,
                'size': file_size,
                'content_type': file.content_type,
                'url': url
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/files', methods=['GET'])
def list_files():
    """List all files in Firebase Storage"""
    try:
        blobs = bucket.list_blobs()
        files = []
        
        for blob in blobs:
            files.append({
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None
            })
        
        return jsonify({
            'success': True,
            'count': len(files),
            'files': files
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
