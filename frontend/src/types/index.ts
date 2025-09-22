// API Types
export interface Session {
  id: string;
  name: string;
  description?: string;
  status: 'created' | 'active' | 'stopped' | 'error';
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  session_id: string;
  content: string;
  message_type: 'user' | 'assistant' | 'tool' | 'system' | 'thinking';
  sender: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface CreateSessionRequest {
  name?: string;
  description?: string;
}

export interface SendMessageRequest {
  content: string;
  message_type?: string;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  data: any;
}

export interface SessionStatusUpdate {
  status: string;
  message?: string;
}

// VNC Types
export interface VNCInfo {
  vnc_url: string;
  vnc_port: number;
  display: string;
}
