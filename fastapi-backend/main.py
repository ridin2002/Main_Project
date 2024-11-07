from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil

app = FastAPI()

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        with open(f"uploaded_videos/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return JSONResponse(content={"message": "File uploaded successfully"})
    except Exception as e:
        return JSONResponse(content={"message": "Failed to upload file"}, status_code=500)
