import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>🏥 Medical Assistant AI</h1>
        <p className="subtitle">Your intelligent healthcare companion</p>
        <p className="description">
          Get personalized medical recommendations and find nearby specialists
        </p>
      </div>

      <div className="features-grid">
        <div className="feature-card" onClick={() => navigate('/symptom-chat')}>
          <div className="feature-icon">💬</div>
          <h2>Symptom Assessment</h2>
          <p>Chat about your symptoms and get medicine recommendations</p>
          <button className="feature-btn">Start Chat</button>
        </div>

        <div className="feature-card" onClick={() => navigate('/document-chat')}>
          <div className="feature-icon">📄</div>
          <h2>Document Analysis</h2>
          <p>Upload prescriptions or medical reports for analysis</p>
          <button className="feature-btn">Upload Document</button>
        </div>

        <div className="feature-card" onClick={() => navigate('/multilingual')}>
          <div className="feature-icon">🌐</div>
          <h2>Multilingual Support</h2>
          <p>Upload documents in Hindi, Tamil, Bengali, and 10+ Indian languages</p>
          <button className="feature-btn">Try Multilingual</button>
        </div>
        
      </div>

      <div className="info-section">
        <h3>✨ Features</h3>
        <ul>
          <li>🤖 AI-powered symptom analysis</li>
          <li>💊 Personalized medicine recommendations</li>
          <li>📍 Find nearby specialists based on your location</li>
          <li>📄 OCR-powered document processing</li>
          <li>🔒 Secure and private conversations</li>
        </ul>
      </div>
    </div>
  );
};

export default Home;
