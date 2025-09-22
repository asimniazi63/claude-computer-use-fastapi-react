import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Grid,
  Paper,
  TextField,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Send as SendIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
} from '@mui/icons-material';

import { sessionAPI, vncAPI } from '../services/api';
import { webSocketService } from '../services/websocket';
import { Session, Message, VNCInfo, WebSocketMessage } from '../types';
import ChatMessage from './ChatMessage';
import VNCViewer from './VNCViewer';
import FileManager from './FileManager';

const SessionView: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // State
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [vncInfo, setVncInfo] = useState<VNCInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [sending, setSending] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionData();
      connectWebSocket();
    }

    return () => {
      webSocketService.disconnect();
    };
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100); // Small delay to ensure DOM is updated
    
    return () => clearTimeout(timer);
  }, [messages]);

  const loadSessionData = async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      
      // Load session, messages, and VNC info in parallel
      const [sessionData, messagesData, vncData] = await Promise.all([
        sessionAPI.getSession(sessionId),
        sessionAPI.getSessionMessages(sessionId),
        vncAPI.getVNCInfo(sessionId),
      ]);

      setSession(sessionData);
      setMessages(messagesData);
      setVncInfo(vncData);
      setError(null);
    } catch (err) {
      setError('Failed to load session data');
      console.error('Error loading session:', err);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = async () => {
    if (!sessionId) return;

    try {
      await webSocketService.connect(sessionId);
      setWsConnected(true);

      // Set up event handlers
      webSocketService.on('message', handleWebSocketMessage);
      webSocketService.on('tool_result', handleWebSocketMessage);
      webSocketService.on('session_status', handleSessionStatusUpdate);
      webSocketService.on('error', handleWebSocketError);

    } catch (err) {
      console.error('WebSocket connection failed:', err);
      setWsConnected(false);
    }
  };

  const handleWebSocketMessage = (wsMessage: WebSocketMessage) => {
    if (wsMessage.type === 'message' && wsMessage.data) {
      const newMessage: Message = wsMessage.data;
      setMessages(prev => {
        // Avoid duplicates
        if (prev.find(m => m.id === newMessage.id)) {
          return prev;
        }
        return [...prev, newMessage];
      });
    } else if (wsMessage.type === 'tool_result' && wsMessage.data) {
      const toolMessage: Message = wsMessage.data;
      setMessages(prev => {
        if (prev.find(m => m.id === toolMessage.id)) {
          return prev;
        }
        return [...prev, toolMessage];
      });
    }
  };

  const handleSessionStatusUpdate = (wsMessage: WebSocketMessage) => {
    if (wsMessage.data && session) {
      setSession(prev => prev ? {
        ...prev,
        status: wsMessage.data.status
      } : null);
    }
  };

  const handleWebSocketError = (wsMessage: WebSocketMessage) => {
    setError(wsMessage.data?.message || 'WebSocket error occurred');
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end',
        inline: 'nearest'
      });
    }
  };

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !sessionId || sending) {
      return;
    }

    try {
      setSending(true);
      
      await sessionAPI.sendMessage(sessionId, {
        content: messageInput.trim(),
        message_type: 'user',
      });

      setMessageInput('');
    } catch (err) {
      setError('Failed to send message');
      console.error('Error sending message:', err);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleStartSession = async () => {
    if (!sessionId) return;

    try {
      await sessionAPI.startSession(sessionId);
    } catch (err) {
      setError('Failed to start session');
      console.error('Error starting session:', err);
    }
  };

  const handleStopSession = async () => {
    if (!sessionId) return;

    try {
      await sessionAPI.stopSession(sessionId);
    } catch (err) {
      setError('Failed to stop session');
      console.error('Error stopping session:', err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!session) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">Session not found</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {session.name}
          </Typography>

          <Chip
            label={session.status}
            color={session.status === 'active' ? 'success' : 'default'}
            sx={{ mr: 2, color: 'white', backgroundColor: 'rgba(255,255,255,0.2)' }}
          />

          {session.status === 'active' ? (
            <Button
              color="inherit"
              startIcon={<StopIcon />}
              onClick={handleStopSession}
            >
              Stop
            </Button>
          ) : (
            <Button
              color="inherit"
              startIcon={<PlayIcon />}
              onClick={handleStartSession}
            >
              Start
            </Button>
          )}
        </Toolbar>
      </AppBar>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ m: 1 }}>
          {error}
        </Alert>
      )}

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex', height: 'calc(100vh - 64px)' }}>
        <Grid container sx={{ height: '100%' }}>
          {/* VNC Viewer */}
          <Grid item xs={12} md={8} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Paper sx={{ flexGrow: 1, m: 1, overflow: 'hidden' }}>
              <VNCViewer vncInfo={vncInfo} />
            </Paper>
          </Grid>

          {/* Right Panel */}
          <Grid item xs={12} md={4} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Chat Section */}
            <Paper sx={{ 
              height: 'calc(100% - 320px)', // Fixed height, leaving space for file manager
              m: 1, 
              display: 'flex', 
              flexDirection: 'column',
              minHeight: '400px' // Minimum height to ensure usability
            }}>
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', flexShrink: 0 }}>
                <Typography variant="h6">
                  Chat Session
                  {wsConnected && (
                    <Chip
                      label="Connected"
                      color="success"
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Typography>
              </Box>

              {/* Messages */}
              <Box sx={{ 
                flexGrow: 1, 
                overflow: 'auto', 
                p: 1,
                display: 'flex',
                flexDirection: 'column',
                // Ensure scrollbar appears when needed
                '&::-webkit-scrollbar': {
                  width: '8px',
                },
                '&::-webkit-scrollbar-track': {
                  backgroundColor: 'rgba(0,0,0,0.1)',
                  borderRadius: '4px',
                },
                '&::-webkit-scrollbar-thumb': {
                  backgroundColor: 'rgba(0,0,0,0.3)',
                  borderRadius: '4px',
                  '&:hover': {
                    backgroundColor: 'rgba(0,0,0,0.5)',
                  },
                },
              }}>
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </Box>

              {/* Message Input */}
              <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', flexShrink: 0 }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    fullWidth
                    placeholder="Type a message to send to Claude..."
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    multiline
                    maxRows={4}
                    disabled={sending}
                  />
                  <IconButton
                    color="primary"
                    onClick={handleSendMessage}
                    disabled={!messageInput.trim() || sending}
                  >
                    {sending ? <CircularProgress size={24} /> : <SendIcon />}
                  </IconButton>
                </Box>
              </Box>
            </Paper>

            {/* File Manager */}
            <Paper sx={{ height: '300px', m: 1, overflow: 'hidden' }}>
              <FileManager sessionId={sessionId!} />
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default SessionView;
