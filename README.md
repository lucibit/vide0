# Vide0 - The Personal Video Upload Server

Application that allows uploading videos from trusted sources and allows sharing links to them.

You can host this on your personal NAS and use it to upload videos and then share them with friends. 


## Development with Cursor

1. Make sure you have Python 3.11+ and pip installed on your system.
2. Open this project in Cursor.
3. Cursor should automatically detect the Python environment. If not, set the Python interpreter to your system Python (or a virtualenv).
4. To install dependencies, run:
```sh
pip install -r requirements.txt
```
5. To run the FastAPI app locally (without Docker):
```sh
uvicorn app.main:app --reload
```

## Using the Upload Client

1. Install the required package:
```sh
pip install requests
```
2. Run the upload client:
```sh
python upload_client.py http://localhost:8000 /path/to/your/video.mp4
```
Replace `/path/to/your/video.mp4` with your video file path.

This will split the file, upload all chunks, and complete the upload process. 

## Running Docker

1. Clear and re-build container
```sh
docker rm -f video-server && docker build -t video-server . 
```
2. run container

```sh
docker run -d \
-p 8000:8000 \
-v /Users/lucianonea/my_videos:/nas/videos \
--name video-server \
video-server
```

## Managing Keys

### Just generate a key
```sh
python upload_client.py generate-key myuser
```

### Generate and upload key to server
```sh
python upload_client.py generate-key myuser --upload --server-url http://localhost:8000
```

### Upload a video
```sh
python upload_client.py upload http://localhost:8000 /path/to/video.mp4 myuser
```