import React, { useState, useEffect } from 'react';
import { uploadMultilingualDocument, chatMultilingual } from '../services/api';
import './MultilingualDashboard.css';

const MultilingualDashboard = () => {
  const [supportedLanguages, setSupportedLanguages] = useState([
    // Most popular languages
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'zh-CN', name: 'Chinese (Simplified)', flag: '🇨🇳' },
    { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
    { code: 'ko', name: 'Korean', flag: '🇰🇷' },
    { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
    { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'ru', name: 'Russian', flag: '🇷🇺' },
    { code: 'it', name: 'Italian', flag: '🇮🇹' },
    { code: 'th', name: 'Thai', flag: '🇹🇭' },
    { code: 'vi', name: 'Vietnamese', flag: '🇻🇳' },
    { code: 'id', name: 'Indonesian', flag: '🇮🇩' },
    { code: 'tr', name: 'Turkish', flag: '🇹🇷' },
    { code: 'nl', name: 'Dutch', flag: '🇳🇱' },
    { code: 'pl', name: 'Polish', flag: '🇵🇱' }
  ]);

  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [sessionId, setSessionId] = useState(null);
  const [documentInfo, setDocumentInfo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fileInputRef = React.useRef(null);

  useEffect(() => {
    fetchSupportedLanguages();
  }, []);

  const fetchSupportedLanguages = async () => {
    try {
      const response = await fetch('http://localhost:5005/medical-api/medicin/supported_languages');
      const data = await response.json();
      setSupportedLanguages(data.languages);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      const response = await uploadMultilingualDocument(file);

      setSessionId(response.session_id);
      setDocumentInfo(response);
      setMessages([{
        role: 'system',
        content: `✅ Document uploaded in ${response.language_name}! You can now ask questions.`
      }]);

      // Auto-select detected language for responses
      setSelectedLanguage(response.detected_language);

    } catch (error) {
      console.error('Error uploading:', error);
      alert(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const userMessage = inputMessage;
    setInputMessage('');

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      setLoading(true);
      const response = await chatMultilingual(sessionId, userMessage, selectedLanguage);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response_translated,
        englishVersion: response.response_english
      }]);

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Sorry, something went wrong.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="multilingual-dashboard">

      <div className="dashboard-header">
        <h1>🌍 Universal Medical Assistant</h1>
        <p>Upload prescriptions in ANY language - 200+ languages supported!</p>
      </div>


      <div className="language-showcase">
        <h3>📚 Supported Languages Include:</h3>
        <div className="language-categories">
          <div className="lang-category">
            <h4>🇪🇺 European</h4>
            <p>Spanish, French, German, Italian, Portuguese, Dutch, Polish, Russian, Greek, Turkish, Swedish, Norwegian...</p>
          </div>
          <div className="lang-category">
            <h4>🇦🇸 Asian</h4>
            <p>Chinese, Japanese, Korean, Thai, Vietnamese, Indonesian, Hindi, Bengali, Tamil, Telugu, Urdu...</p>
          </div>
          <div className="lang-category">
            <h4>🌎 Middle East & Africa</h4>
            <p>Arabic, Hebrew, Persian, Swahili, Afrikaans...</p>
          </div>
          <div className="lang-category">
            <h4>✨ And 180+ More!</h4>
            <p>Auto-detected automatically</p>
          </div>
        </div>
      </div>



      {!sessionId ? (
        <div className="upload-section">
          <div className="language-selector">
            <label>Supported Languages:</label>
            <div className="language-grid">
              {supportedLanguages.map(lang => (
                <span key={lang.code} className="language-badge">
                  {lang.name}
                </span>
              ))}
            </div>
          </div>

          <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
            {uploading ? (
              <div className="uploading">
                <div className="spinner"></div>
                <p>Processing multilingual document...</p>
              </div>
            ) : (
              <>
                <div className="upload-icon">📤</div>
                <h3>Upload Document in Any Indian Language</h3>
                <p>Hindi, Tamil, Bengali, Telugu, and more...</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
      ) : (
        <>
          <div className="document-info-card">
            <h3>📄 {documentInfo.filename}</h3>
            <p>Detected Language: <strong>{documentInfo.language_name}</strong></p>
            <p>Pages: {documentInfo.pages}</p>
          </div>

          <div className="response-language-selector">
            <label>Choose Response Language:</label>
            <select value={selectedLanguage} onChange={(e) => setSelectedLanguage(e.target.value)}>
              {supportedLanguages.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">
                  <p>{msg.content}</p>
                  {msg.englishVersion && selectedLanguage !== 'en' && (
                    <details className="english-version">
                      <summary>View English version</summary>
                      <p>{msg.englishVersion}</p>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="chat-input-area">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask about your document (in English)..."
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

export default MultilingualDashboard;
