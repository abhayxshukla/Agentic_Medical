import React, { useState } from 'react';
import Home from './Home';
import ChatInterface from './ChatInterface';
import * as api from './api';
import './App.css'; // <-- Import the new enhanced CSS

function App() {
  const [chatMode, setChatMode] = useState(null); // 'symptom' or 'document'
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documentInfo, setDocumentInfo] = useState(null); // {filename, pages}
  const [error, setError] = useState(null);

  // Resets everything to go back to the Home screen
  const endCurrentSession = async () => {
    try {
      await api.deleteSession(sessionId);
      console.log('Session deleted:', sessionId);
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
    setChatMode(null);
    setSessionId(null);
    setMessages([]);
    setDocumentInfo(null);
    setError(null);
  };

  // -- Handlers for Home.js --

  // Called when "Analyze Symptoms" is clicked
  const handleStartSymptomChat = async () => {
    try {
      setError(null);
      const { data } = await api.startSymptomChat();
      setSessionId(data.session_id);
      setMessages([
        { sender: 'bot', text: data.response }
      ]);
      setChatMode('symptom');
    } catch (err) {
      setError('Failed to start symptom chat. Please try again.');
      console.error(err);
    }
  };

  // Called when a file is uploaded on the Home screen
  const handleUploadDocument = async (file) => {
    try {
      setError(null);
      const { data } = await api.uploadDocument(file);
      setSessionId(data.session_id);
      setDocumentInfo({ filename: data.filename, pages: data.pages });
      setMessages([
        { sender: 'system', text: `Uploaded "${data.filename}" (${data.pages} pages).` },
        { sender: 'bot', text: 'How can I help you with this document?' }
      ]);
      setChatMode('document');
    } catch (err) {
      setError('File upload failed. Please try again.');
      console.error(err);
    }
  };

  // -- Handlers for ChatInterface.js --

  // Called when a new message is sent from the chat input
  const handleSendMessage = async (text) => {
    // Add user's message immediately
    setMessages(prev => [...prev, { sender: 'user', text }]);

    try {
      let response;
      if (chatMode === 'symptom') {
        response = await api.sendSymptomMessage(sessionId, text);
        const { data } = response;
        
        if (data.status === 'ongoing') {
          setMessages(prev => [...prev, { sender: 'bot', text: data.response }]);
        } else if (data.status === 'complete') {
          // Add the final recommendation as two separate messages
          setMessages(prev => [
            ...prev,
            { sender: 'system', text: 'Symptom analysis complete.' },
            { sender: 'bot', text: data.medicine_recommendation }
          ]);
        }
      } else if (chatMode === 'document') {
        response = await api.sendDocumentMessage(sessionId, text);
        setMessages(prev => [...prev, { sender: 'bot', text: response.data.response }]);
      }

    } catch (err) {
      setMessages(prev => [
        ...prev,
        { sender: 'system', text: 'Error: Could not get a response.' }
      ]);
      console.error(err);
    }
  };


  return (
    <div className="app-container">
      {!chatMode ? (
        <Home
          onStartSymptomChat={handleStartSymptomChat}
          onUploadDocument={handleUploadDocument}
          error={error}
        />
      ) : (
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          onEndSession={endCurrentSession}
          chatMode={chatMode}
          documentInfo={documentInfo}
        />
      )}
    </div>
  );
}

export default App;