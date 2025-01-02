import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

axios.defaults.withCredentials = true;

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_URL}/files`);
      if (response.status === 200) {
        setUploadedFiles(response.data);
        setError('');
      } else {
        setError('Unexpected response from server');
      }
    } catch (err) {
      console.error('Fetch error:', err);
      if (err.response) {
        // Server responded with a status other than 2xx
        setError(err.response.data.message || 'Error fetching files');
      } else if (err.request) {
        // Request was made but no response received
        setError('No response from server. Please check your network connection.');
      } else {
        // Something else happened
        setError('An unexpected error occurred. Please try again later.');
      }
    } finally {
      setIsLoading(false);
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

    setIsUploading(true);
    setError('');
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('pdfs', file);
    });

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data && response.data.files) {
        setSelectedFiles([]);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        await fetchFiles();  // Refresh the file list
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.message || 'Error uploading files');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (filename) => {
    try {
      await axios.delete(`${API_URL}/files/${encodeURIComponent(filename)}`);
      fetchFiles();
    } catch (err) {
      setError('Error deleting file');
      console.error('Delete error:', err);
    }
  };

  const handleDeleteAll = async () => {
    try {
      await axios.delete(`${API_URL}/files`);
      setUploadedFiles([]);
      setError('');
    } catch (err) {
      setError('Error deleting all files');
      console.error('Delete all error:', err);
    }
  };

  const handleExtractText = async () => {
    try {
      setIsExtracting(true);
      setError('');
      
      const response = await axios.post(`${API_URL}/extract-text`, {}, {
        timeout: 3000000
      });
      
      if (response.data.error) {
        setError(response.data.error);
      } else {
        // Store the extracted text in state
        setExtractedText(response.data.result);
        
        // Optionally scroll to the results
        document.getElementById('extraction-results')?.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (err) {
      console.error('Extraction error:', err);
      setError(err.response?.data?.message || 'Error extracting text from PDFs');
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="App">
      <h1>PDF File Upload to S3</h1>
      
      <div className="upload-section">
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileSelect}
          ref={fileInputRef}
          disabled={isUploading}
        />
        <button 
          onClick={handleUpload} 
          disabled={selectedFiles.length === 0 || isUploading}
        >
          {isUploading ? 'Uploading...' : 'Upload Files'}
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
        <div className="uploaded-files-header">
          <h2>Uploaded Files</h2>
          <div className="header-buttons">
            {!isLoading && uploadedFiles.length > 0 && (
              <>
                <button 
                  onClick={handleExtractText}
                  className="extract-button"
                  disabled={isExtracting || isUploading}
                >
                  {isExtracting ? 'Generating...' : 'Generate Cheat Sheet'}
                </button>
                <button 
                  onClick={handleDeleteAll}
                  className="delete-all-button"
                  disabled={isUploading || isExtracting}
                >
                  Delete All
                </button>
              </>
            )}
          </div>
        </div>
        {isLoading ? (
          <div className="loading-message">Loading files...</div>
        ) : (
          <ul>
            {uploadedFiles.map((file) => (
              <li key={file._id}>
                {file.filename}
                <button 
                  onClick={() => handleDelete(file._id)}
                  disabled={isUploading}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {extractedText && (
        <div id="extraction-results" className="extraction-results">
          <h2>Generated Cheat Sheet</h2>
          <pre className="extracted-text">{extractedText}</pre>
          <div className="overleaf-link">
            <a 
              href="https://www.overleaf.com" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Click here to paste this LaTeX code into Overleaf and get your PDF
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 