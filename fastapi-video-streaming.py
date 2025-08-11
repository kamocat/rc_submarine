import asyncio
from fastapi import FastAPI, Response, Request, WebSocket
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import threading
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional, Union
from pydantic import BaseModel
import json


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    try:
        yield
    except asyncio.exceptions.CancelledError as error:
        print(error.args)
    finally:
        camera.release()
        print("Camera resource released.")

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Camera:
    """
    A class to handle video capture from a camera.
    """

    def __init__(self, url: Optional[Union[str, int]] = 0) -> None:
        """
        Initialize the camera.

        :param camera_index: Index of the camera to use.
        """
        self.cap = cv2.VideoCapture(url, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        width=1920
        height=1080
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.lock = threading.Lock()

    def get_frame(self) -> bytes:
        """
        Capture a frame from the camera.

        :return: JPEG encoded image bytes.
        """
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                return b''

            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                return b''

            return jpeg.tobytes()

    def release(self) -> None:
        """
        Release the camera resource.
        """
        with self.lock:
            if self.cap.isOpened():
                self.cap.release()


async def gen_frames() -> AsyncGenerator[bytes, None]:
    """
    An asynchronous generator function that yields camera frames.

    :yield: JPEG encoded image bytes.
    """
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


@app.get("/video")
async def video_feed() -> StreamingResponse:
    """
    Video streaming route.

    :return: StreamingResponse with multipart JPEG frames.
    """
    return StreamingResponse(
        gen_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@app.get("/snapshot")
async def snapshot() -> Response:
    """
    Snapshot route to get a single frame.

    :return: Response with JPEG image.
    """
    frame = camera.get_frame()
    if frame:
        return Response(content=frame, media_type="image/jpeg")
    else:
        return Response(status_code=404, content="Camera frame not available.")

@app.get("/")
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
            request=request, name="base.html"
    )

class JoystickPosition(BaseModel):
    x: float
    y: float
    speed: float
    angle: float

@app.websocket("/joystick")
async def joystick(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        try:
            data = json.loads(data)
            print(data)
        except Exception as e:
            print(e)

async def main():
    """
    Main entry point to run the Uvicorn server.
    """
    config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)

    # Run the server
    await server.serve()

if __name__ == '__main__':
    # Usage example: Streaming default camera for local webcam:
    # camera = Camera()

    # Usage example: Streaming the camera for a specific camera index:
    camera = Camera(0)

    # Usage example 3: Streaming an IP camera:
    # camera = Camera('rtsp://user:password@ip_address:port/')

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user.")
