import React, { useState, useEffect, useRef } from 'react';

function ChatInterface({ messages, onSendMessage, onEndSession, chatMode, documentInfo }) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Ref to scroll to the bottom of the messages
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check if the chat is complete (for symptom flow)
  const isChatComplete = messages.some(m => m.sender === 'system' && m.text.includes('complete'));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || isChatComplete) return;

    setIsLoading(true);
    await onSendMessage(input);
    setInput('');
    setIsLoading(false);
  };

  return (
    <div className="chat-window">
      <header className="chat-header">
        <div>
          <h2>Medical Assistant</h2>
          {chatMode === 'document' && documentInfo && (
            <span className="document-title">Analyzing: {documentInfo.filename}</span>
          )}
        </div>
        <button onClick={onEndSession} className="btn-danger">New Chat</button>
      </header>

      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}-bubble`}>
            {/* Simple markdown for bolding */}
            {msg.text.split('**').map((part, i) =>
              i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message bot-bubble loading-bubble">
            <span></span><span></span><span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isChatComplete ? "Chat complete. Start a new chat." : "Type your message..."}
          disabled={isLoading || isChatComplete}
        />
        <button type="submit" className="btn-send" disabled={isLoading || isChatComplete || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;