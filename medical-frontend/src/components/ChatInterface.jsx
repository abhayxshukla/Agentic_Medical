import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, FileText, Home, Trash2, User, Bot } from 'lucide-react';
import apiService from '../services/api';
import '../styles/ChatInterface.css';

const ChatInterface = ({ sessionId, chatType, documentInfo, onReset, initialMessage }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (initialMessage) {
      setMessages([initialMessage]);
    }
  }, [initialMessage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!loading) {
      inputRef.current?.focus();
    }
  }, [loading]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      let response;

      if (chatType === 'symptom') {
        response = await apiService.chatSymptoms(sessionId, userMessage.content);

        if (response.status === 'complete') {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: response.medicine_recommendation,
              type: 'medicine_recommendation',
              timestamp: new Date().toISOString(),
            },
          ]);
          setIsComplete(true);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: response.response,
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      } else {
        response = await apiService.chatWithDocument(sessionId, userMessage.content);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.response,
            document: response.document,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          content: error.response?.data?.detail || 'Failed to send message. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleDeleteSession = async () => {
    if (confirm('Are you sure you want to end this session?')) {
      try {
        await apiService.deleteSession(sessionId);
        onReset();
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-content">
          <div>
            <h1>{chatType === 'symptom' ? 'Symptom Assessment' : 'Document Analysis'}</h1>
            {documentInfo && (
              <div className="chat-header-info">
                <FileText size={16} />
                <span>{documentInfo.filename}</span>
              </div>
            )}
          </div>
          <div className="chat-header-actions">
            <button onClick={handleDeleteSession} className="icon-btn" title="Delete Session">
              <Trash2 size={20} color="var(--gray-600)" />
            </button>
            <button onClick={onReset} className="icon-btn" title="New Session">
              <Home size={20} color="var(--gray-600)" />
            </button>
          </div>
        </div>
      </div>

      <div className="messages-container">
        <div className="messages-wrapper">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              {msg.role !== 'user' && (
                <div className="avatar bot">
                  <Bot size={24} />
                </div>
              )}

              <div className={`message-bubble ${msg.role} ${msg.type === 'medicine_recommendation' ? 'recommendation' : ''}`}>
                {msg.type === 'medicine_recommendation' && (
                  <div className="recommendation-header">
                    <FileText size={16} />
                    <span>Medicine Recommendation</span>
                  </div>
                )}
                <div className="message-content">{msg.content}</div>
                {msg.document && (
                  <div className="message-source">
                    <FileText size={12} />
                    <span>Source: {msg.document}</span>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="avatar user">
                  <User size={24} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message-row assistant loading-indicator">
              <div className="avatar bot">
                <Bot size={24} />
              </div>
              <div className="loading-bubble">
                <Loader2 size={20} className="spinner" color="var(--primary)" />
                <span>AI is thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          {isComplete && chatType === 'symptom' ? (
            <div className="completion-message">
              <p>Assessment complete! Start a new session for another consultation.</p>
              <button onClick={onReset} className="btn btn-primary">
                New Consultation
              </button>
            </div>
          ) : (
            <div className="chat-input-form">
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={loading}
                className="input-field"
              />
              <button
                onClick={sendMessage}
                disabled={loading || !inputMessage.trim()}
                className="btn btn-primary"
              >
                <Send size={20} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
