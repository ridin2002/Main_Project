import React, { useState } from 'react';
import axios from 'axios';

const VideoUpload = () => {
    const [videoFile, setVideoFile] = useState(null);

    const handleFileChange = (e) => {
        setVideoFile(e.target.files[0]);
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', videoFile);

        try {
            const response = await axios.post('http://localhost:8000/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            alert('File uploaded successfully');
        } catch (error) {
            alert('Failed to upload file');
            console.error(error);
        }
    };

    return (
        <form onSubmit={handleUpload}>
            <input type="file" accept="video/*" onChange={handleFileChange} />
            <button type="submit">Upload Video</button>
        </form>
    );
};

export default VideoUpload;
