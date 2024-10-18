# Detailed Code Explanation

## Imports and Setup

```python
import asyncio
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import cv2
import threading
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Tuple, Optional, Union
```

This section imports necessary libraries:
- `asyncio` for asynchronous programming
- `FastAPI` for creating the web server
- `cv2` (OpenCV) for video capture and processing
- `threading` for thread-safe camera access
- Various typing utilities for type hinting
- `uvicorn` for running the ASGI server

## Lifespan Context Manager

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    except asyncio.exceptions.CancelledError as error:
        print(error.args)
    finally:
        camera.release()
        print("Camera resource released.")

app = FastAPI(lifespan=lifespan)
```

This context manager ensures proper resource management:
- It handles startup and shutdown events for the FastAPI application.
- On shutdown, it releases the camera resource, preventing resource leaks.

## Camera Class

```python
class Camera:
    def __init__(self, url: Optional[Union[str, int]] = 0) -> None:
        self.cap = cv2.VideoCapture(url)
        self.lock = threading.Lock()

    def get_frame(self) -> bytes:
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                return b''
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                return b''
            return jpeg.tobytes()

    def release(self) -> None:
        with self.lock:
            if self.cap.isOpened():
                self.cap.release()
```

The `Camera` class encapsulates video capture functionality:
- It initializes a video capture object with a given URL or camera index.
- `get_frame()` captures a frame, converts it to JPEG, and returns the bytes.
- `release()` safely releases the camera resource.
- Thread locks ensure thread-safe access to the camera.

## Frame Generator

```python
async def gen_frames() -> AsyncGenerator[bytes, None]:
    try:
        while True:
            frame = camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                break
            await asyncio.sleep(0)
    except (asyncio.CancelledError, GeneratorExit):
        print("Frame generation cancelled.")
    finally:
        print("Frame generator exited.")
```

This asynchronous generator function:
- Continuously yields frames from the camera.
- Formats each frame as part of a multipart HTTP response.
- Handles cancellation and cleanup gracefully.

## API Endpoints

```python
@app.get("/video")
async def video_feed() -> StreamingResponse:
    return StreamingResponse(
        gen_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.get("/snapshot")
async def snapshot() -> Response:
    frame = camera.get_frame()
    if frame:
        return Response(content=frame, media_type="image/jpeg")
    else:
        return Response(status_code=404, content="Camera frame not available.")
```

Two endpoints are defined:
1. `/video`: Streams continuous video using `StreamingResponse`.
2. `/snapshot`: Returns a single frame as a JPEG image.

## Main Function and Server Startup

```python
async def main():
    config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    camera = Camera()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user.")
```

The main function:
- Configures and starts the Uvicorn server.
- Initializes the camera with the specified URL.
- Runs the server asynchronously and handles keyboard interrupts for graceful shutdown.

