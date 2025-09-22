import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

import { sessionAPI } from '../services/api';
import { Session, CreateSessionRequest } from '../types';

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [newSessionDescription, setNewSessionDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const sessionData = await sessionAPI.getSessions();
      setSessions(sessionData);
      setError(null);
    } catch (err) {
      setError('Failed to load sessions');
      console.error('Error loading sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!newSessionName.trim()) {
      return;
    }

    try {
      setCreating(true);
      const sessionData: CreateSessionRequest = {
        name: newSessionName.trim(),
        description: newSessionDescription.trim() || undefined,
      };

      const newSession = await sessionAPI.createSession(sessionData);
      setSessions(prev => [newSession, ...prev]);
      setCreateDialogOpen(false);
      setNewSessionName('');
      setNewSessionDescription('');
      
      // Navigate to the new session
      navigate(`/session/${newSession.id}`);
    } catch (err) {
      setError('Failed to create session');
      console.error('Error creating session:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      await sessionAPI.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
    } catch (err) {
      setError('Failed to delete session');
      console.error('Error deleting session:', err);
    }
  };

  const handleStartSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      await sessionAPI.startSession(sessionId);
      loadSessions(); // Refresh to get updated status
    } catch (err) {
      setError('Failed to start session');
      console.error('Error starting session:', err);
    }
  };

  const handleStopSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      await sessionAPI.stopSession(sessionId);
      loadSessions(); // Refresh to get updated status
    } catch (err) {
      setError('Failed to stop session');
      console.error('Error stopping session:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'stopped':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Energent AI (Challenge)
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Task History
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Agent Task
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={3}>
            {sessions.map((session) => (
              <Grid item xs={12} sm={6} md={4} key={session.id}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    '&:hover': {
                      elevation: 4,
                      transform: 'translateY(-2px)',
                    },
                    transition: 'all 0.2s ease-in-out',
                  }}
                  onClick={() => navigate(`/session/${session.id}`)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Typography variant="h6" component="h2" noWrap>
                        {session.name}
                      </Typography>
                      <Chip
                        label={session.status}
                        color={getStatusColor(session.status) as any}
                        size="small"
                      />
                    </Box>
                    
                    {session.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {session.description}
                      </Typography>
                    )}

                    <Typography variant="caption" color="text.secondary">
                      Created: {formatDate(session.created_at)}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      Messages: {session.message_count}
                    </Typography>
                  </CardContent>

                  <CardActions>
                    {session.status === 'active' ? (
                      <Button
                        size="small"
                        startIcon={<StopIcon />}
                        onClick={(e) => handleStopSession(session.id, e)}
                      >
                        Stop
                      </Button>
                    ) : (
                      <Button
                        size="small"
                        startIcon={<PlayIcon />}
                        onClick={(e) => handleStartSession(session.id, e)}
                      >
                        Start
                      </Button>
                    )}
                    <Button
                      size="small"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={(e) => handleDeleteSession(session.id, e)}
                    >
                      Delete
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}

            {sessions.length === 0 && (
              <Grid item xs={12}>
                <Box
                  sx={{
                    textAlign: 'center',
                    py: 8,
                    color: 'text.secondary',
                  }}
                >
                  <Typography variant="h6" gutterBottom>
                    No sessions yet
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Create your first agent task to get started
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateDialogOpen(true)}
                    sx={{ mt: 2 }}
                  >
                    New Agent Task
                  </Button>
                </Box>
              </Grid>
            )}
          </Grid>
        )}
      </Container>

      {/* Create Session Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Agent Task</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Task Name"
            fullWidth
            variant="outlined"
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newSessionDescription}
            onChange={(e) => setNewSessionDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateSession}
            variant="contained"
            disabled={!newSessionName.trim() || creating}
          >
            {creating ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MainLayout;
