import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
  Build as ToolIcon,
  Info as SystemIcon,
  Psychology as ThinkingIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const getMessageIcon = () => {
    switch (message.message_type) {
      case 'user':
        return <PersonIcon />;
      case 'assistant':
        return <BotIcon />;
      case 'tool':
        return <ToolIcon />;
      case 'system':
        return <SystemIcon />;
      case 'thinking':
        return <ThinkingIcon />;
      default:
        return <BotIcon />;
    }
  };

  const getMessageColor = () => {
    switch (message.message_type) {
      case 'user':
        return 'primary';
      case 'assistant':
        return 'secondary';
      case 'tool':
        return 'warning';
      case 'system':
        return 'info';
      case 'thinking':
        return 'default';
      default:
        return 'default';
    }
  };

  const isUserMessage = message.message_type === 'user';
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString();
  };

  const renderContent = () => {
    if (message.message_type === 'thinking') {
      return (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2" color="text.secondary">
              Claude is thinking...
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </Typography>
          </AccordionDetails>
        </Accordion>
      );
    }

    if (message.message_type === 'tool') {
      return (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Chip
              icon={<ToolIcon />}
              label={`Tool: ${message.sender}`}
              color="warning"
              size="small"
            />
            {message.metadata?.is_error && (
              <Chip
                label="Error"
                color="error"
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </Box>
          
          <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
          </Typography>

          {message.metadata?.base64_image && (
            <Box sx={{ mt: 1 }}>
              <img
                src={`data:image/png;base64,${message.metadata.base64_image}`}
                alt="Tool output"
                style={{ maxWidth: '100%', height: 'auto' }}
              />
            </Box>
          )}
        </Box>
      );
    }

    // Use markdown rendering for assistant messages, plain text for others
    if (message.message_type === 'assistant') {
      return (
        <Box sx={{ 
          '& pre': { 
            backgroundColor: 'rgba(0, 0, 0, 0.04)', 
            padding: 1, 
            borderRadius: 1, 
            overflow: 'auto',
            fontSize: '0.875rem',
            fontFamily: 'monospace'
          },
          '& code': { 
            backgroundColor: 'rgba(0, 0, 0, 0.04)', 
            padding: '2px 4px', 
            borderRadius: '4px',
            fontSize: '0.875rem',
            fontFamily: 'monospace'
          },
          '& blockquote': { 
            borderLeft: '4px solid #ccc', 
            paddingLeft: 2, 
            margin: '16px 0',
            fontStyle: 'italic'
          },
          '& h1, & h2, & h3, & h4, & h5, & h6': {
            marginTop: 2,
            marginBottom: 1
          },
          '& p': {
            marginBottom: 1
          },
          '& ul, & ol': {
            paddingLeft: 3
          }
        }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </Box>
      );
    }

    return (
      <Typography variant="body1" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
        {message.content}
      </Typography>
    );
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUserMessage ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: isUserMessage ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
          maxWidth: '80%',
        }}
      >
        <Avatar
          sx={{
            bgcolor: getMessageColor() === 'primary' ? 'primary.main' : 'grey.500',
            width: 32,
            height: 32,
            mx: 1,
          }}
        >
          {getMessageIcon()}
        </Avatar>

        <Paper
          elevation={1}
          sx={{
            p: 2,
            backgroundColor: isUserMessage ? 'primary.50' : 'grey.50',
            borderRadius: 2,
            maxWidth: '100%',
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {message.sender}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatTime(message.created_at)}
            </Typography>
          </Box>

          {renderContent()}
        </Paper>
      </Box>
    </Box>
  );
};

export default ChatMessage;
