# Building a FastAPI Web Server to Stream Video from Camera

This Python script implements a FastAPI-based web server for streaming video from various camera sources. It utilizes OpenCV for video capture and processing and employs asynchronous programming for efficient frame generation. The script defines a Camera class for thread-safe video capture and includes two main endpoints: one for continuous video streaming and another for single-frame snapshots. The server uses a lifespan context manager for proper resource handling, ensuring the camera is released on shutdown. The main function configures and runs a Uvicorn server to serve the FastAPI application. The script is flexible, allowing for different camera sources (local webcams, IP cameras), and can be easily adapted for various video streaming needs in web applications.

![image](https://github.com/user-attachments/assets/643c9095-67a9-44b6-92db-f1f508236be2)

![image](https://github.com/user-attachments/assets/6a3865fe-5423-40f6-b1c3-aa66277e97d9)

## Features

- Stream video from local webcams or IP cameras
- Capture and serve individual snapshots
- Asynchronous frame generation for efficient streaming
- Thread-safe camera access
- Graceful shutdown and resource management

## Requirements

- Python 3.7+
- FastAPI
- OpenCV (cv2)
- uvicorn

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/fastapi-video-streaming.git
   cd fastapi-video-streaming
   ```

2. Install the required packages:
   ```
   pip install fastapi opencv-python-headless uvicorn
   ```

## Usage

1. Modify the camera initialization in the `__main__` section of the script:

   ```python
   # For local webcam:
   camera = Camera()

   # For a specific camera index:
   camera = Camera(0)

   # For an IP camera:
   camera = Camera('rtsp://user:password@ip_address:port/')
   ```

2. Run the server:
   ```
   python fastapi_video_server.py
   ```

3. Access the video stream in your browser or video player:
   - Video stream: `http://localhost:8000/video`
   - Snapshot: `http://localhost:8000/snapshot`

## API Endpoints

- `/video`: Returns a continuous stream of JPEG frames
- `/snapshot`: Returns a single JPEG frame

## Configuration

The server runs on `0.0.0.0:8000` by default. To change this, modify the `uvicorn.Config` parameters in the `main()` function.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
