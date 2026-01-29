import axios from 'axios';

const BASE_URL = 'http://localhost:5005/medical-api/medicin';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Symptom Chat APIs
export const startSymptomChat = async () => {
  const response = await api.post('/start_symptom_chat');
  return response.data;
};

export const chatSymptoms = async (sessionId, message) => {
  const response = await api.post('/chat_symptoms', {
    session_id: sessionId,
    message: message,
  });
  return response.data;
};

export const chatSymptomsWithLocation = async (sessionId, message, pinCode) => {
  const response = await api.post('/chat_symptoms_with_location', {
    session_id: sessionId,
    message: message,
    pin_code: pinCode,
  });
  return response.data;
};

// Document Chat APIs
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload_document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const chatWithDocument = async (sessionId, message) => {
  const response = await api.post('/chat_with_document', {
    session_id: sessionId,
    message: message,
  });
  return response.data;
};

export const chatDocumentWithLocation = async (sessionId, message, pinCode) => {
  const response = await api.post('/chat_document_with_location', {
    session_id: sessionId,
    message: message,
    pin_code: pinCode,
  });
  return response.data;
};

// Location APIs
export const findNearbyHospitals = async (pinCode, specialty = null, radiusKm = 10) => {
  const response = await api.post('/find_nearby_hospitals', {
    pin_code: pinCode,
    specialty: specialty,
    radius_km: radiusKm,
  });
  return response.data;
};

export const uploadMultilingualDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload_multilingual_document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const chatMultilingual = async (sessionId, message, responseLanguage = 'en') => {
  const response = await api.post('/chat_multilingual', {
    session_id: sessionId,
    message: message,
    response_language: responseLanguage
  });
  return response.data;
};

// Session Management
export const deleteSession = async (sessionId) => {
  const response = await api.post('/delete_session', {
    session_id: sessionId,
  });
  return response.data;
};

export default api;
