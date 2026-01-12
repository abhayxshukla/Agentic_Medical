import { useState } from 'react';
import ModeSelector from './components/ModeSelector';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import apiService from './services/api';

function App() {
  const [view, setView] = useState('selector');
  const [sessionId, setSessionId] = useState(null);
  const [chatType, setChatType] = useState(null);
  const [documentInfo, setDocumentInfo] = useState(null);
  const [initialMessage, setInitialMessage] = useState(null);

  const handleStartSymptomChat = async () => {
    try {
      const response = await apiService.startSymptomChat();
      setSessionId(response.session_id);
      setChatType('symptom');
      setInitialMessage({
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      });
      setView('chat');
    } catch (error) {
      alert('Failed to start symptom chat. Please try again.');
      console.error(error);
    }
  };

  const handleShowUpload = () => {
    setView('upload');
  };

  const handleUploadSuccess = (result) => {
    setSessionId(result.session_id);
    setChatType('document');
    setDocumentInfo({
      filename: result.filename,
      pages: result.pages,
    });
    setView('chat');
  };

  const handleReset = () => {
    setView('selector');
    setSessionId(null);
    setChatType(null);
    setDocumentInfo(null);
    setInitialMessage(null);
  };

  return (
    <>
      {view === 'selector' && (
        <ModeSelector
          onSelectSymptom={handleStartSymptomChat}
          onShowUpload={handleShowUpload}
        />
      )}

      {view === 'upload' && (
        <FileUpload
          onUploadSuccess={handleUploadSuccess}
          onCancel={handleReset}
        />
      )}

      {view === 'chat' && (
        <ChatInterface
          sessionId={sessionId}
          chatType={chatType}
          documentInfo={documentInfo}
          onReset={handleReset}
          initialMessage={initialMessage}
        />
      )}
    </>
  );
}

export default App;
