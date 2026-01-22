import React from 'react';
import { useNavigate } from 'react-router-dom';
import SymptomChat from '../components/SymptomChat';
import './ChatPage.css';

const SymptomChatPage = () => {
  const navigate = useNavigate();

  return (
    <div className="chat-page">
      <button className="back-btn" onClick={() => navigate('/')}>
        ← Back to Home
      </button>
      <SymptomChat />
    </div>
  );
};

export default SymptomChatPage;
