import React, { useState, useEffect, useRef } from 'react';
import { startSymptomChat, chatSymptoms, chatSymptomsWithLocation } from '../services/api';
import LocationSearch from './LocationSearch';
import HospitalList from './HospitalList';
import './SymptomChat.css';

const SymptomChat = () => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [medicineRec, setMedicineRec] = useState(null);
  const [symptomsSummary, setSymptomsSummary] = useState(null);
  const [nearbyHospitals, setNearbyHospitals] = useState(null);
  const [loadingHospitals, setLoadingHospitals] = useState(false);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initializeChat();
  }, []);

  const initializeChat = async () => {
    try {
      setLoading(true);
      const response = await startSymptomChat();
      setSessionId(response.session_id);
      setMessages([{
        role: 'assistant',
        content: response.response
      }]);
    } catch (error) {
      console.error('Error starting chat:', error);
      alert('Failed to start chat. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage;
    setInputMessage('');
    
    // Add user message to chat
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage
    }]);

    try {
      setLoading(true);
      const response = await chatSymptoms(sessionId, userMessage);

      // Add assistant response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response || response.medicine_recommendation
      }]);

      // Check if complete
      if (response.status === 'complete') {
        setIsComplete(true);
        setMedicineRec(response.medicine_recommendation);
        setSymptomsSummary(response.symptoms_summary);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Sorry, something went wrong. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSearch = async (pinCode) => {
    setLoadingHospitals(true);
    try {
      const response = await chatSymptomsWithLocation(
        sessionId,
        symptomsSummary || 'Find nearby hospitals',
        pinCode
      );

      if (response.location_info) {
        setNearbyHospitals(response.location_info);
      } else {
        alert('No hospitals found nearby. Try a different PIN code.');
      }
    } catch (error) {
      console.error('Error finding hospitals:', error);
      alert('Failed to find hospitals. Please try again.');
    } finally {
      setLoadingHospitals(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="symptom-chat-container">
      <div className="chat-header">
        <h2>💬 Symptom Assessment Chat</h2>
        <p>Describe your symptoms and get personalized recommendations</p>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              <p>{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {isComplete && medicineRec && (
        <div className="medicine-recommendation">
          <h3>💊 Medicine Recommendation</h3>
          <p>{medicineRec}</p>
        </div>
      )}

      {isComplete && (
        <>
          <LocationSearch 
            onSearch={handleLocationSearch}
            loading={loadingHospitals}
          />
          <HospitalList locationInfo={nearbyHospitals} />
        </>
      )}

      {!isComplete && (
        <div className="chat-input-area">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your symptoms..."
            disabled={loading}
          />
          <button onClick={handleSendMessage} disabled={loading || !inputMessage.trim()}>
            Send
          </button>
        </div>
      )}
    </div>
  );
};

export default SymptomChat;
