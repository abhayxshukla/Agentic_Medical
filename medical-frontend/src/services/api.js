import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5005/medical-api/medicin';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  startSymptomChat: async () => {
    const response = await api.post('/start_symptom_chat');
    return response.data;
  },

  chatSymptoms: async (sessionId, message) => {
    const response = await api.post('/chat_symptoms', {
      session_id: sessionId,
      message: message,
    });
    return response.data;
  },

  uploadDocument: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload_document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  chatWithDocument: async (sessionId, message) => {
    const response = await api.post('/chat_with_document', {
      session_id: sessionId,
      message: message,
    });
    return response.data;
  },

  deleteSession: async (sessionId) => {
    const response = await api.post('/delete_session', {
      session_id: sessionId,
    });
    return response.data;
  },
};

export default apiService;
