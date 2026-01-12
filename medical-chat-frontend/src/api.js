import axios from 'axios';

// Your main.py runs on port 5005
const API_BASE_URL = 'http://localhost:5005/medical-api/medicin';

// Create an axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * FLOW 1: Symptom Chat
 */

// POST /start_symptom_chat
export const startSymptomChat = () => {
  return apiClient.post('/start_symptom_chat');
};

// POST /chat_symptoms
export const sendSymptomMessage = (sessionId, message) => {
  return apiClient.post('/chat_symptoms', {
    session_id: sessionId,
    message: message,
  });
};

/**
 * FLOW 2: Document Chat
 */

// POST /upload_document
export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return apiClient.post('/upload_document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// POST /chat_with_document
export const sendDocumentMessage = (sessionId, message) => {
  return apiClient.post('/chat_with_document', {
    session_id: sessionId,
    message: message,
  });
};

/**
 * UTILITY
 */

// POST /delete_session
export const deleteSession = (sessionId) => {
  if (!sessionId) return Promise.resolve(); // No session to delete
  return apiClient.post('/delete_session', { session_id: sessionId });
};