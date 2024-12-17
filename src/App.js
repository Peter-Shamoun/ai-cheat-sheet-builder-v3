import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000';

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/files`);
      setUploadedFiles(response.data);
    } catch (err) {
      setError('Error fetching files');
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 10) {
      setError('You can only upload up to 10 files at once');
      return;
    }

    const invalidFiles = files.filter(file => file.type !== 'application/pdf');
    if (invalidFiles.length > 0) {
      setError('Only PDF files are allowed');
      return;
    }

    setSelectedFiles(files);
    setError('');
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select files to upload');
      return;
    }

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('pdfs', file);
    });

    try {
      await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setSelectedFiles([]);
      fetchFiles();
      setError('');
    } catch (err) {
      setError('Error uploading files');
    }
  };

  const handleDelete = async (fileId) => {
    try {
      await axios.delete(`${API_URL}/files/${fileId}`);
      fetchFiles();
    } catch (err) {
      setError('Error deleting file');
    }
  };

  return (
    <div className="App">
      <h1>PDF File Upload</h1>
      
      <div className="upload-section">
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileSelect}
        />
        <button onClick={handleUpload} disabled={selectedFiles.length === 0}>
          Upload Files
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="selected-files">
        <h2>Selected Files</h2>
        <ul>
          {selectedFiles.map((file, index) => (
            <li key={index}>{file.name}</li>
          ))}
        </ul>
      </div>

      <div className="uploaded-files">
        <h2>Uploaded Files</h2>
        <ul>
          {uploadedFiles.map((file) => (
            <li key={file._id}>
              {file.filename}
              <button onClick={() => handleDelete(file._id)}>Delete</button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App; 