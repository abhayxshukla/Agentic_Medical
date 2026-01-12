import React, { useState } from 'react';

function Home({ onStartSymptomChat, onUploadDocument, error }) {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(null); // 'symptom' or 'document'

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUploadClick = async () => {
    if (!file) {
      alert('Please select a file first.');
      return;
    }
    setIsLoading('document');
    await onUploadDocument(file);
    setIsLoading(null);
  };

  const handleSymptomClick = async () => {
    setIsLoading('symptom');
    await onStartSymptomChat();
    setIsLoading(null);
  };

  return (
    <div className="home-container">
      <header className="home-header">
        <img src="/logo192.png" alt="logo" className="home-logo" />
        <h1>Medical Assistant</h1>
        <p>Your AI-powered health companion</p>
      </header>
      
      {error && <div className="error-message">{error}</div>}

      <div className="home-options">
        <div className="option-card">
          <h2>Analyze Symptoms</h2>
          <p>Have a conversation with our AI to analyze your symptoms and get recommendations.</p>
          <button 
            onClick={handleSymptomClick} 
            disabled={isLoading}
            className="btn btn-primary"
          >
            {isLoading === 'symptom' ? 'Starting...' : 'Start Symptom Chat'}
          </button>
        </div>

        <div className="option-card">
          <h2>Analyze Document</h2>
          <p>Upload a medical report, prescription, or scan to get an analysis.</p>
          <input 
            type="file" 
            id="file-upload"
            onChange={handleFileChange} 
            accept=".pdf,.png,.jpg,.jpeg,.docx" 
            disabled={isLoading}
            className="file-input"
          />
          <button 
            onClick={handleUploadClick} 
            disabled={isLoading || !file}
            className="btn btn-secondary"
          >
            {isLoading === 'document' ? 'Uploading...' : 'Upload and Chat'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home;