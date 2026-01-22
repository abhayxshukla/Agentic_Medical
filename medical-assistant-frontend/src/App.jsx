import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import SymptomChatPage from './pages/SymptomChatPage';
import DocumentChatPage from './pages/DocumentChatPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/symptom-chat" element={<SymptomChatPage />} />
          <Route path="/document-chat" element={<DocumentChatPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
