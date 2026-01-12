import { MessageSquare, FileText, Activity, AlertCircle } from 'lucide-react';
import '../styles/ModeSelector.css';

const ModeSelector = ({ onSelectSymptom, onShowUpload }) => {
  return (
    <div className="mode-selector">
      <div className="mode-container">
        <div className="mode-header">
          <div className="mode-header-icon">
            <div className="icon-circle icon-circle-large" style={{ backgroundColor: 'var(--primary)' }}>
              <Activity size={32} color="white" />
            </div>
          </div>
          <h1>Medical AI Assistant</h1>
          <p>How can I help you today?</p>
        </div>

        <div className="mode-grid">
          <div className="card card-hover mode-card" onClick={onSelectSymptom}>
            <div className="flex flex-col items-center">
              <div className="icon-circle mb-2" style={{ backgroundColor: '#DBEAFE' }}>
                <MessageSquare size={32} color="var(--primary)" />
              </div>
              <h2>Describe Symptoms</h2>
              <p>Chat with our AI assistant to analyze your symptoms and get medicine recommendations</p>
              <button className="btn btn-primary">Start Conversation</button>
            </div>
          </div>

          <div className="card card-hover mode-card" onClick={onShowUpload}>
            <div className="flex flex-col items-center">
              <div className="icon-circle mb-2" style={{ backgroundColor: '#CCFBF1' }}>
                <FileText size={32} color="var(--secondary)" />
              </div>
              <h2>Upload Document</h2>
              <p>Upload medical reports, prescriptions, or documents for AI analysis and recommendations</p>
              <button className="btn btn-secondary">Upload Document</button>
            </div>
          </div>
        </div>

        <div className="card info-card">
          <div className="flex gap-2">
            <div className="icon-circle" style={{ backgroundColor: '#93C5FD', width: '32px', height: '32px' }}>
              <AlertCircle size={16} color="var(--primary)" />
            </div>
            <div>
              <h3 style={{ marginBottom: '8px', fontWeight: '600' }}>Important Notice</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-700)' }}>
                This AI assistant provides general medical information and suggestions. 
                Always consult with a qualified healthcare professional for proper diagnosis and treatment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModeSelector;
