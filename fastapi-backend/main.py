from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from ultralytics import YOLO
import cv2
import shutil
import os

app = FastAPI()

# Directories for storing videos
upload_dir = "uploaded_videos"
output_dir = "output_videos"
os.makedirs(upload_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Initialize YOLO model
try:
    model = YOLO('yolov8n.pt')  # Ensure 'yolov8n.pt' is in the working directory
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Endpoint to upload video."""
    file_path = f"{upload_dir}/{file.filename}"
    
    try:
        # Save the uploaded video file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse(content={"message": "File uploaded successfully", "file_path": file_path})
    
    except Exception as e:
        print(f"Error while uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@app.post("/detect-and-draw/")
async def detect_and_draw(file_path: str):
    """Detect objects in frames, draw bounding boxes, and save as new video at 10 FPS."""
    try:
        # Ensure YOLO model is loaded
        if model is None:
            raise HTTPException(status_code=500, detail="YOLO model is not initialized.")

        # Check if the video file exists
        if not os.path.exists(file_path):
            return JSONResponse(content={"message": "File not found"}, status_code=404)

        # Open the video for reading
        capture = cv2.VideoCapture(file_path)
        frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_fps = int(capture.get(cv2.CAP_PROP_FPS))

        # Set target FPS to 10
        target_fps = 10
        skip_frames = max(1, original_fps // target_fps)

        # Prepare video writer for output
        output_path = f"{output_dir}/processed_{os.path.basename(file_path)}"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        output_video = cv2.VideoWriter(output_path, fourcc, target_fps, (frame_width, frame_height))

        frame_count = 0
        while True:
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

                # Write the processed frame to the output video
                output_video.write(frame)

            frame_count += 1

        # Release resources
        capture.release()
        output_video.release()
        
        return JSONResponse(content={"message": "Objects detected and bounding boxes drawn successfully", "output_path": output_path})
    
    except Exception as e:
        print(f"Error during detection and drawing: {e}")
        return JSONResponse(content={"message": "Failed to process video", "error": str(e)}, status_code=500)

@app.get("/download-video/{video_filename}")
async def download_video(video_filename: str):
    """Endpoint to download the processed video."""
    video_path = f"{output_dir}/{video_filename}"
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4", filename=video_filename)
    else:
        return JSONResponse(content={"message": "File not found"}, status_code=404)
