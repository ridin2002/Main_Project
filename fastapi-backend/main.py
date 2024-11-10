from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import shutil
import os
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific domains if possible
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories for storing videos
upload_dir = "uploaded_videos"
output_dir = "output_videos"
os.makedirs(upload_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Initialize YOLO model
model = None
try:
    model = YOLO('yolov8n.pt')  # Ensure 'yolov8n.pt' is in the working directory
except Exception as e:
    print(f"Error loading YOLO model: {e}")

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Endpoint to upload video."""
    file_path = f"{upload_dir}/{file.filename}"
    
    try:
        # Save the uploaded video file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse(content={"message": "Video uploaded successfully", "file_path": file_path})
    
    except Exception as e:
        print(f"Error while uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@app.websocket("/ws/process-video")
async def process_video(websocket: WebSocket):
    """WebSocket endpoint to stream processed video frames at 10 FPS."""
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        file_path = data.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            await websocket.send_json({"error": "Invalid file path"})
            await websocket.close()
            return
        
        if model is None:
            await websocket.send_json({"error": "YOLO model not loaded"})
            await websocket.close()
            return

        # Open video capture
        capture = cv2.VideoCapture(file_path)
        if not capture.isOpened():
            await websocket.send_json({"error": "Unable to open video file"})
            await websocket.close()
            return
        
        frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_fps = int(capture.get(cv2.CAP_PROP_FPS))

        # Calculate the frame skipping interval for target 10 FPS
        target_fps = 10
        skip_frames = max(1, original_fps // target_fps)

        frame_count = 0
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break

            # Process every nth frame to achieve 10 FPS
            if frame_count % skip_frames == 0:
                # Run YOLO detection on the frame
                results = model(frame)

                # Draw bounding boxes for each detected object
                for box in results[0].boxes:
                    if box is not None and hasattr(box, 'xyxy') and hasattr(box, 'conf') and hasattr(box, 'cls'):
                        x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                        confidence = float(box.conf[0])  # Confidence score
                        class_index = int(box.cls[0].item())  # Class index
                        label = results[0].names[class_index]  # Detected class label

                        # Draw the bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Encode frame as JPEG and send via WebSocket
                _, buffer = cv2.imencode(".jpg", frame)
                if _:
                    frame_data = buffer.tobytes()
                    await websocket.send_bytes(frame_data)
                else:
                    await websocket.send_json({"error": "Error encoding frame"})
                    break

                # Send progress update every second
                progress = int((frame_count / total_frames) * 100)
                await websocket.send_json({"progress": progress})

            frame_count += 1

        # Close capture when finished
        capture.release()
        await websocket.send_json({"message": "Video processing complete"})

    except WebSocketDisconnect:
        print("WebSocket connection closed by client")

    except Exception as e:
        print(f"Error during video processing: {e}")
        await websocket.send_json({"error": "Error during video processing"})
        await websocket.close()