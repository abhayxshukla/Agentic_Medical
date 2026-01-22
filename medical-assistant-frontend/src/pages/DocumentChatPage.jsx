import React from 'react';
import { useNavigate } from 'react-router-dom';
import DocumentChat from '../components/DocumentChat';
import './ChatPage.css';

const DocumentChatPage = () => {
  const navigate = useNavigate();

  return (
    <div className="chat-page">
      <button className="back-btn" onClick={() => navigate('/')}>
        ← Back to Home
      </button>
      <DocumentChat />
    </div>
  );
};

export default DocumentChatPage;
