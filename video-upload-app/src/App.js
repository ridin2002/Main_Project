import React, { useState, useEffect, useRef } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [frameSrc, setFrameSrc] = useState(null);
  const [progress, setProgress] = useState(0); 
  const websocket = useRef(null);

  // Handle file change event
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  // Handle file upload and send the video to the backend
  const handleUpload = async () => {
    if (!selectedFile) return alert("Please select a video file!");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        // Start processing after video upload
        startProcessing(data.file_path);
      } else {
        alert("Error uploading video: " + data.message);
      }
    } catch (error) {
      alert("An error occurred: " + error);
    }
  };

  // Start processing video via WebSocket
  const startProcessing = (filePath) => {
    setIsProcessing(true);
    setProgress(0);

    // Initialize WebSocket connection
    websocket.current = new WebSocket("ws://localhost:8000/ws/process-video");

    websocket.current.onopen = () => {
      console.log("WebSocket connection opened");
      // Send the file path to start processing
      websocket.current.send(JSON.stringify({ file_path: filePath }));
    };

    websocket.current.onmessage = (event) => {
      if (typeof event.data === "string") {
        const message = JSON.parse(event.data);
        if (message.message === "Video processing complete") {
          setIsProcessing(false);
          setProgress(100);  // Complete progress bar when processing is done
          websocket.current.close();
        } else if (message.progress) {
          // Smoothly animate progress using requestAnimationFrame
          requestAnimationFrame(() => setProgress(message.progress));
        }
      } else {
        const blob = new Blob([event.data], { type: "image/jpeg" });
        const frameUrl = URL.createObjectURL(blob);
        setFrameSrc(frameUrl);
      }
    };

    websocket.current.onclose = () => {
      console.log("WebSocket connection closed");
      setIsProcessing(false);
    };

    websocket.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsProcessing(false);
    };
  };

  // Cleanup WebSocket connection when component unmounts
  useEffect(() => {
    return () => {
      if (websocket.current) {
        websocket.current.close();
      }
    };
  }, []);

  return (
    <div
      style={{
        backgroundColor: "#3E2723",
        color: "#fff",
        fontFamily: "Arial, sans-serif",
        minHeight: "100vh",
        padding: "10px 20px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #fff",
          paddingBottom: "10px",
        }}
      >
        <h1 style={{ margin: "0" }}>Modular Traffic Violation Detection</h1>
        <div>
          <button style={headerButtonStyle}>Dashboard</button>
          <button style={headerButtonStyle}>Library</button>
          <button style={headerButtonStyle}>AI Model Market</button>
          <button style={headerButtonStyle}>Help</button>
          <button style={headerButtonStyle}>New model</button>
        </div>
      </div>

      <h2 style={{ fontSize: "20px", marginBottom: "10px", marginTop: "10px" }}>
        Real-time traffic violation detection
      </h2>
      <p style={{ fontSize: "14px", marginBottom: "20px" }}>
        Upload a video or use your camera to detect violations in real time.
      </p>

      {/* File Input and Upload Button */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "20px",
          marginBottom: "20px",
        }}
      >
        <label style={{ ...buttonStyle, cursor: "pointer" }}>
          Choose File
          <input
            type="file"
            onChange={handleFileChange}
            accept="video/mp4"
            style={{ display: "none" }}
          />
        </label>
        <span style={{ color: "#fff", fontSize: "16px", marginLeft: "10px" }}>
          {selectedFile ? selectedFile.name : "No file chosen"}
        </span>
        <button
          style={{
            ...buttonStyle,
            backgroundColor: "#9C27B0",
          }}
          onClick={handleUpload}
        >
          Upload Video  
        </button>
      </div>

      {/* Progress Bar */}
      {isProcessing && (
        <div style={{ marginTop: "20px", textAlign: "center" }}>
          <p>Processing video</p>
          <div
            style={{
              backgroundColor: "#5D4037",
              height: "10px",
              width: "80%",
              margin: "0 auto",
              borderRadius: "5px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                backgroundColor: "#D32F2F",
                height: "100%",
                width: `${progress}%`,
                transition: "width 0.3s ease",
              }}
            ></div>
          </div>
          <p style={{ color: "#fff", fontSize: "12px", marginTop: "5px" }}>
            {progress}%
          </p>
        </div>
      )}

      {/* Display Real-time Video Frames */}
      <div style={{ textAlign: "center", marginTop: "20px" }}>
        <h3>Live feed</h3>
        <div
          style={{
            position: "relative",
            width: "80%",
            margin: "0 auto",
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          {frameSrc ? (
            <img
              src={frameSrc}
              alt="Processed frame"
              style={{ width: "90%", borderRadius: "8px" }}
            />
          ) : (
            <div
              style={{
                width: "100%",
                height: "400px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                backgroundColor: "#333",
                borderRadius: "8px",
              }}
            >
              {isProcessing ? "Processing video..." : "Real-time Feed"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const headerButtonStyle = {
  backgroundColor: "transparent",
  color: "#fff",
  border: "none",
  margin: "0 10px",
  padding: "10px 20px",
  fontSize: "16px",
  cursor: "pointer",
};

const buttonStyle = {
  backgroundColor: "#9C27B0",
  color: "#fff",
  border: "none",
  padding: "15px 30px",
  fontSize: "18px",
  borderRadius: "5px",
  cursor: "pointer",
  display: "inline-block",
};

export default App