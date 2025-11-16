import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'mp4'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH', 'credential.json'))
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

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
    Optional parameter: folder (string) - specify folder path in Firebase Storage
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
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{extension}"
        
        # Construct storage path with folder if provided
        if folder:
            # Remove leading/trailing slashes and construct path
            folder = folder.strip('/')
            storage_path = f"{folder}/{unique_filename}"
        else:
            storage_path = unique_filename
        
        # Upload to Firebase Storage
        blob = bucket.blob(storage_path)
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
                'original_filename': filename,
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
