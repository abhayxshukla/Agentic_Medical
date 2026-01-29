import React, { useState, useRef, useEffect } from 'react';
import { uploadDocument, chatWithDocument, chatDocumentWithLocation } from '../services/api';
import LocationSearch from './LocationSearch';
import HospitalList from './HospitalList';
import './DocumentChat.css';


const DocumentChat = () => {
  const [sessionId, setSessionId] = useState(null);
  const [documentName, setDocumentName] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [nearbyHospitals, setNearbyHospitals] = useState(null);
  const [loadingHospitals, setLoadingHospitals] = useState(false);
  const [showLocationSearch, setShowLocationSearch] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, showLocationSearch]);


  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;


    try {
      setUploading(true);
      const response = await uploadDocument(file);
      setSessionId(response.session_id);
      setDocumentName(response.filename);
      setMessages([{
        role: 'system',
        content: `Document "${response.filename}" uploaded successfully! (${response.pages} pages). You can now ask questions about it.`
      }]);
      setShowLocationSearch(false); // Reset location search on new upload
      setNearbyHospitals(null); // Clear previous hospital results
    } catch (error) {
      console.error('Error uploading document:', error);
      alert(error.response?.data?.detail || 'Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
    }
  };


  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading || !sessionId) return;


    const userMessage = inputMessage;
    setInputMessage('');
    
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage
    }]);


    try {
      setLoading(true);
      const response = await chatWithDocument(sessionId, userMessage);


      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response
      }]);

      // Show location search after assistant responds
      setShowLocationSearch(true);
      
      scrollToBottom();
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
    if (!sessionId) return;

    setLoadingHospitals(true);
    setNearbyHospitals(null); // Clear previous results

    try {
      // Get the last assistant message as context
      const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant');
      const contextMessage = lastAssistantMessage?.content || 'Find nearby specialists based on this prescription.';

      const response = await chatDocumentWithLocation(
        sessionId,
        contextMessage,
        pinCode
      );


      // Only add new response if it's different from the last one
      if (response.response && response.response !== lastAssistantMessage?.content) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: response.response
        }]);
      }


      if (response.location_info) {
        setNearbyHospitals(response.location_info);
        
        // Add a system message about hospitals found
        setMessages(prev => [...prev, {
          role: 'system',
          content: `📍 Found ${response.location_info.hospitals.length} nearby healthcare facilities${
            response.location_info.specialty_detected 
              ? ` for ${response.location_info.specialty_detected}` 
              : ''
          }.`
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'system',
          content: '⚠️ No specialist recommendation found. Try asking about the diagnosis first.'
        }]);
      }
    } catch (error) {
      console.error('Error finding hospitals:', error);
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Failed to find nearby hospitals. Please try again.'
      }]);
    } finally {
      setLoadingHospitals(false);
      scrollToBottom();
    }
  };


  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };


  return (
    <div className="document-chat-container">
      <div className="chat-header">
        <h2>📄 Document Analysis Chat</h2>
        <p>Upload prescription, blood report, or medical document</p>
      </div>


      {!sessionId ? (
        <div className="upload-section">
          <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
            {uploading ? (
              <div className="uploading">
                <div className="spinner"></div>
                <p>Uploading and processing...</p>
              </div>
            ) : (
              <>
                <div className="upload-icon">📎</div>
                <h3>Click to Upload Document</h3>
                <p>Supported: PDF, DOCX, PNG, JPG, JPEG (Max 16 MB)</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.docx,.doc"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
      ) : (
        <>
          <div className="document-info">
            <p>📄 Analyzing: <strong>{documentName}</strong></p>
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

          {/* Show location search only after at least one assistant response */}
          {showLocationSearch && messages.some(m => m.role === 'assistant') && (
            <LocationSearch 
              onSearch={handleLocationSearch}
              loading={loadingHospitals}
            />
          )}

          {/* Show hospital list if available */}
          <HospitalList locationInfo={nearbyHospitals} />


          <div className="chat-input-area">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your document..."
              disabled={loading}
            />
            <button onClick={handleSendMessage} disabled={loading || !inputMessage.trim()}>
              Send
            </button>
          </div>
        </>
      )}
    </div>
  );
};


export default DocumentChat;
