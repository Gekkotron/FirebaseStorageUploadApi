# Firebase Storage File Upload API

A simple Flask API to upload files (JPG, MP4) to Firebase Storage.

## Features

- Upload JPG, JPEG, and MP4 files to Firebase Storage
- File size validation (max 100MB)
- Generate signed URLs for uploaded files
- List all files in storage
- CORS enabled for cross-origin requests
- Health check endpoint

## Prerequisites

- Python 3.8 or higher
- Firebase project with Storage enabled
- Firebase Admin SDK credentials (`credential.json`)

## Setup

1. **Clone or navigate to the project directory**

2. **Copy your Firebase credentials**
   
   Place your `credential.json` file in the project root directory.

3. **Create environment file**
   
   Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set your Firebase Storage bucket:
   ```
   FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
   ```

4. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Local Development

Start the Flask development server:

```bash
python app.py
```

The API will be available at `http://localhost:5001`

### Option 2: Docker

**Build and run with Docker:**
```bash
docker build -t firebase-storage-api .
docker run -p 5001:5001 --env-file .env -v $(pwd)/credential.json:/app/credential.json:ro firebase-storage-api
```

**Or use Docker Compose:**
```bash
docker compose up -d
```

**View logs:**
```bash
docker compose logs -f
```

**Stop the container:**
```bash
docker compose down
```

## API Endpoints

### Health Check
```
GET /health
```
Returns API health status.

### Upload File
```
POST /upload
```
Upload a file to Firebase Storage.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: 
  - `file` (required): JPG, JPEG, or MP4 file
  - `folder` (optional): Folder path in Firebase Storage (e.g., "images" or "videos/2025")

**Example using curl:**
```bash
# Upload to root directory
curl -X POST -F "file=@/path/to/your/file.jpg" http://localhost:5001/upload

# Upload to a specific folder
curl -X POST -F "file=@/path/to/your/file.jpg" -F "folder=images" http://localhost:5001/upload

# Upload to nested folders
curl -X POST -F "file=@/path/to/your/video.mp4" -F "folder=videos/2025/november" http://localhost:5001/upload
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "data": {
    "filename": "unique-filename.jpg",
    "storage_path": "images/unique-filename.jpg",
    "original_filename": "file.jpg",
    "size": 123456,
    "content_type": "image/jpeg",
    "url": "https://storage.googleapis.com/..."
  }
}
```

### List Files
```
GET /files
```
List all files in Firebase Storage.

**Response:**
```json
{
  "success": true,
  "count": 2,
  "files": [
    {
      "name": "file1.jpg",
      "size": 123456,
      "content_type": "image/jpeg",
      "created": "2025-11-16T10:00:00",
      "updated": "2025-11-16T10:00:00"
    }
  ]
}
```

## Configuration

Edit `.env` to configure:

- `FLASK_ENV`: Set to `development` or `production`
- `PORT`: Server port (default: 5001)
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase credentials (default: credential.json)
- `FIREBASE_STORAGE_BUCKET`: Your Firebase Storage bucket name

## File Restrictions

- Allowed formats: JPG, JPEG, MP4
- Maximum file size: 100MB

## Security Notes

- The `.gitignore` file excludes `credential.json` to prevent committing sensitive credentials
- Signed URLs expire after 1 hour by default
- Consider adding authentication for production use
- Review Firebase Storage security rules

## Usage Examples

### Upload Examples with curl

**Upload a JPG image:**
```bash
curl -X POST -F "file=@photo.jpg" http://localhost:5001/upload
```

**Upload to a specific folder:**
```bash
curl -X POST \
  -F "file=@profile.jpg" \
  -F "folder=users/avatars" \
  http://localhost:5001/upload
```

**Upload a video:**
```bash
curl -X POST -F "file=@demo.mp4" -F "folder=videos" http://localhost:5001/upload
```

**Upload with verbose output:**
```bash
curl -v -X POST -F "file=@image.jpg" http://localhost:5001/upload
```

**Save response to file:**
```bash
curl -X POST -F "file=@document.jpg" http://localhost:5001/upload -o response.json
```

**Upload and pretty-print JSON response (with jq):**
```bash
curl -X POST -F "file=@photo.jpg" -F "folder=gallery" http://localhost:5001/upload | jq
```

## Development

To modify allowed file types, update the `ALLOWED_EXTENSIONS` set in `app.py`:
```python
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'mp4', 'png'}  # Add more types
```

To change max file size, update `MAX_FILE_SIZE` in `app.py`:
```python
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
```

## License

MIT
