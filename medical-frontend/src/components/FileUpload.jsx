import { useState } from 'react';
import { Upload, File, X, AlertCircle, CheckCircle } from 'lucide-react';
import apiService from '../services/api';
import '../styles/FileUpload.css';

const FileUpload = ({ onUploadSuccess, onCancel }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const allowedTypes = {
    'application/pdf': 'PDF',
    'image/png': 'PNG',
    'image/jpeg': 'JPG/JPEG',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
  };

  const MAX_FILE_SIZE = 16 * 1024 * 1024;

  const validateFile = (file) => {
    if (!allowedTypes[file.type]) {
      return 'Invalid file type. Please upload PDF, PNG, JPG, or DOCX files.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 16MB.';
    }
    return null;
  };

  const handleFileSelect = (selectedFile) => {
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      return;
    }
    setFile(selectedFile);
    setError(null);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setProgress(0);

    try {
      const result = await apiService.uploadDocument(file, (percent) => {
        setProgress(percent);
      });
      onUploadSuccess(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-content">
        <div className="card">
          <div className="upload-header">
            <h2>Upload Medical Document</h2>
            <button onClick={onCancel} className="icon-btn">
              <X size={24} color="var(--gray-600)" />
            </button>
          </div>

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`drop-zone ${dragActive ? 'active' : ''}`}
          >
            <div className="flex flex-col items-center">
              <div className="icon-circle mb-2" style={{ backgroundColor: '#DBEAFE' }}>
                <Upload size={32} color="var(--primary)" />
              </div>
              <h3>{file ? file.name : 'Drop your file here or click to browse'}</h3>
              <p>Supported formats: PDF, PNG, JPG, DOCX (Max 16MB)</p>
              
              {/* Fixed file input */}
              <input
                type="file"
                id="file-input"
                className="file-input"
                accept=".pdf,.png,.jpg,.jpeg,.docx"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
                disabled={uploading}
              />
              <label htmlFor="file-input" className="btn btn-secondary" style={{ marginTop: '16px', cursor: 'pointer' }}>
                Choose File
              </label>
            </div>
          </div>

          {file && !uploading && (
            <div className="file-info">
              <div className="file-info-content">
                <File size={20} color="var(--primary)" />
                <div className="file-info-text">
                  <h4>{file.name}</h4>
                  <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button onClick={() => setFile(null)} className="icon-btn">
                <X size={20} color="var(--gray-600)" />
              </button>
            </div>
          )}

          {uploading && (
            <div className="progress-container">
              <div className="progress-header">
                <span>Uploading...</span>
                <span className="progress-percent">{progress}%</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          )}

          {error && (
            <div className="alert alert-error">
              <AlertCircle size={20} />
              <p>{error}</p>
            </div>
          )}

          {progress === 100 && !error && (
            <div className="alert alert-success">
              <CheckCircle size={20} />
              <p>Document uploaded successfully!</p>
            </div>
          )}

          {file && !uploading && (
            <button onClick={handleUpload} className="btn btn-primary mt-3" style={{ width: '100%' }}>
              Upload and Analyze
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
