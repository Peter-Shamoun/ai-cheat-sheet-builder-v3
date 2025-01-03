import React, { useState } from 'react';
import './App.css';

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 10) {
      setError('You can only upload up to 10 files at once');
      return;
    }

    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
    const oversizedFiles = files.filter(file => file.size > MAX_FILE_SIZE);
    if (oversizedFiles.length > 0) {
      setError(`The following files exceed the 10MB limit: ${oversizedFiles.map(f => f.name).join(', ')}`);
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

  const handleUpload = () => {
    if (selectedFiles.length === 0) {
      setError('Please select files to upload');
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      // Add files to uploadedFiles state
      setUploadedFiles(prevFiles => [...prevFiles, ...selectedFiles]);
      
      // Clear selection
      setSelectedFiles([]);
      // Clear file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (err) {
      setError('Error uploading files');
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = (filename) => {
    setUploadedFiles(prevFiles => 
      prevFiles.filter(file => file.name !== filename)
    );
  };

  const handleDeleteAll = () => {
    setUploadedFiles([]);
    setExtractedText('');
  };

  const handleExtractText = async () => {
    try {
      setIsGenerating(true);
      setProgress(0);
      const text_list = [];
      setError('');
      
      // First API call: Process each file sequentially to extract text
      for (const file of uploadedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://159.54.182.115:5000/pdf/extract', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`Error processing ${file.name}: ${response.statusText}`);
        }

        const text = await response.text();
        text_list.push(text);
      }
      setProgress(20); // 1/5 complete

      // Second API call: Send the collected texts to get topics
      const topicsResponse = await fetch('http://159.54.182.115:5000/topics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text_list })
      });

      if (!topicsResponse.ok) {
        throw new Error(`Error getting topics: ${topicsResponse.statusText}`);
      }

      const topic_list = await topicsResponse.text();
      setProgress(40); // 2/5 complete

      // Third API call: Summarize the topics
      const summarizeResponse = await fetch('http://159.54.182.115:5000/topics/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          topic_list: topic_list
        })
      });

      if (!summarizeResponse.ok) {
        throw new Error(`Error summarizing topics: ${summarizeResponse.statusText}`);
      }

      const summaryText = await summarizeResponse.text();
      setProgress(60); // 3/5 complete
      
      // Fourth API call: Get LaTeX file
      const latexResponse = await fetch('http://159.54.182.115:5000/latex', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          topic_twelve: summaryText
        })
      });

      if (!latexResponse.ok) {
        throw new Error(`Error generating LaTeX: ${latexResponse.statusText}`);
      }

      const latexText = await latexResponse.text();
      setExtractedText(latexText);
      setProgress(80); // 4/5 complete

      // Fifth API call: Generate PDF from LaTeX
      const pdfResponse = await fetch('http://159.54.182.115:5000/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          template: latexText
        })
      });

      if (!pdfResponse.ok) {
        throw new Error(`Error generating PDF: ${pdfResponse.statusText}`);
      }

      // Handle PDF blob and open in new window
      const blob = await pdfResponse.blob();
      const file = window.URL.createObjectURL(blob);
      window.location.assign(file);
      setProgress(100); // 5/5 complete
      
      // Scroll to results
      document.getElementById('extraction-results')?.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      setError(`Error processing: ${err.message}`);
      console.error('Processing error:', err);
    } finally {
      setIsGenerating(false);
      setTimeout(() => setProgress(0), 1000); // Reset progress after 1 second
    }
  };

  return (
    <div className="App">
      <h1>AI Cheat Sheet Generator</h1>
      
      <div className="upload-section">
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileSelect}
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
            {uploadedFiles.length > 0 && (
              <>
                <button 
                  onClick={handleExtractText}
                  className="extract-button"
                  disabled={isUploading || isGenerating}
                >
                  {isGenerating ? 'Generating...' : 'Generate Cheat Sheet'}
                </button>
                <button 
                  onClick={handleDeleteAll}
                  className="delete-all-button"
                  disabled={isUploading || isGenerating}
                >
                  Delete All
                </button>
              </>
            )}
          </div>
        </div>
        <ul>
          {uploadedFiles.map((file, index) => (
            <li key={index}>
              {file.name}
              <button 
                onClick={() => handleDelete(file.name)}
                disabled={isUploading || isGenerating}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
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

      {isGenerating && (
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-text">
            {progress === 20 && "Extracting text from PDFs..."}
            {progress === 40 && "Analyzing topics..."}
            {progress === 60 && "Summarizing content..."}
            {progress === 80 && "Generating LaTeX..."}
            {progress === 100 && "Creating PDF..."}
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 