import axios from 'axios';
import { Session, Message, CreateSessionRequest, SendMessageRequest, VNCInfo } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8501';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Session API
export const sessionAPI = {
  // Get all sessions
  getSessions: async (): Promise<Session[]> => {
    const response = await api.get('/api/sessions');
    return response.data.sessions;
  },

  // Create a new session
  createSession: async (data: CreateSessionRequest): Promise<Session> => {
    const response = await api.post('/api/sessions', data);
    return response.data;
  },

  // Get a specific session
  getSession: async (sessionId: string): Promise<Session> => {
    const response = await api.get(`/api/sessions/${sessionId}`);
    return response.data;
  },

  // Delete a session
  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/api/sessions/${sessionId}`);
  },

  // Start a session
  startSession: async (sessionId: string): Promise<void> => {
    await api.post(`/api/sessions/${sessionId}/start`);
  },

  // Stop a session
  stopSession: async (sessionId: string): Promise<void> => {
    await api.post(`/api/sessions/${sessionId}/stop`);
  },

  // Get session messages
  getSessionMessages: async (sessionId: string): Promise<Message[]> => {
    const response = await api.get(`/api/sessions/${sessionId}/messages`);
    return response.data.messages;
  },

  // Send a message to a session
  sendMessage: async (sessionId: string, data: SendMessageRequest): Promise<Message> => {
    const response = await api.post(`/api/sessions/${sessionId}/messages`, data);
    return response.data;
  },
};

// VNC API
export const vncAPI = {
  // Get VNC connection info
  getVNCInfo: async (sessionId: string): Promise<VNCInfo> => {
    const response = await api.get(`/api/vnc/${sessionId}`);
    return response.data;
  },
};

export default api;
